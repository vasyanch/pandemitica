import json
import os
import time

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import View
from google.cloud import bigquery, storage

from .forms import SignupForm, LoadFileForm, LoginForm
from .models import File, FileType


class IndexView(View):
    template_name = 'load_files/index.html'

    def get(self, request, *args, **kwargs):
        context = {'user': request.user}
        return render(request, self.template_name, context)


class SelectFileTypeView(View):
    template_name = 'load_files/select_file_type.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = {'file_types': FileType.objects.order_by('id').all()}

    def get(self, request, *args, **kwargs):
        self.context['user'] = request.user
        if not self.context['user'].is_authenticated:
            self.context['error'] = 'You need authorization to load file'
        return render(request, self.template_name, self.context)


class LoadFileView(View):
    template_name = 'load_files/load_file.html'
    form = LoadFileForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = {'error': '', 'load_success': False}

    def get(self, request, *args, **kwargs):
        self.context['user'] = request.user
        self.context['file_type'] = FileType.objects.get(file_type=self.kwargs['file_type'])
        if self.context['user'].is_authenticated:
            self.context['form'] = self.form()
        else:
            self.context['error'] = 'You need authorization to load file'
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            form = self.form(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                self.context['load_success'] = True
                return render(request, self.template_name, self.context)
            else:
                self.context['error'] = 'Invalid file format'
        else:
            self.context['aut_error'] = 'You need authorization to load file'
        return render(request, self.template_name, self.context)


class FileProcessingView(View):
    template_name = 'load_files/file_processing.html'
    template_name_load_result = 'load_files/files_load_result.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = {'error': ''}

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            user_files = File.objects.filter(user_id=user.id).all()
            if user_files:
                files_path = {file.file_type.file_type: file.get_path for file in user_files}
                self.context['load_storage_result'] = self.load_files_to_storage(files_path)
                if all([res[0] for res in self.context['load_storage_result'].values()]):
                    self.context['load_bigquery_result'] = self.load_to_bigquery(self.context['load_storage_result'])
                    self.context['load_amplitude_result'] = self.load_to_amplitude()
                else:
                    return render(request, self.template_name_load_result, self.context)
                return render(request, self.template_name_load_result, self.context)
            else:
                self.context['error'] = 'You need load file'
        else:
            self.context['error'] = 'You need authorization to process file'
        return render(request, self.template_name, self.context)

    @staticmethod
    def load_files_to_storage(files_path: dict) -> dict:
        ans = {key: [] for key in files_path.keys()}
        with open(os.path.join(settings.BASE_DIR, settings.GOOGLE_STORAGE_CRED), encoding='utf8') as cred_file:
            google_storage_cred = json.load(cred_file)
        storage_client = storage.Client.from_service_account_json(
            settings.GOOGLE_STORAGE_CRED, project=google_storage_cred['project_id']
        )
        for file_type, file_path in files_path.items():
            try:
                storage_path = f"gs://{settings.GOOGLE_BUCKET_NAME}/{file_type}"
                bucket_name = settings.GOOGLE_BUCKET_NAME
                file_basename = os.path.basename(file_path)
                path_glob = f"gs://{storage_path}/{file_basename}"

                if storage_client.lookup_bucket(bucket_name) is not None:
                    bucket = storage_client.get_bucket(bucket_name)
                else:
                    raise ValueError('There is no bucket "{}"'.format(bucket_name))
                blob = bucket.blob(path_glob)
                blob.upload_from_filename(file_path)
                ans[file_type] = [True, path_glob]
            except Exception as e:
                ans[file_type] = [False, e]
        return ans

    @staticmethod
    def load_to_bigquery(files: dict):
        ans = {key: [] for key in files.keys()}
        client = bigquery.Client.from_service_account_json(settings.PANDEMITICA_GOOGLE_CLOUD_CRED,
                                                           project=settings.PANDEMITICA_GOOGLE_CLOUD_PROJECT)
        dataset_ref = client.get_dataset(settings.PANDEMITICA_GOOGLE_BIGQUERY_DATASET)
        for file_type, path in files.items():
            try:
                job_config = bigquery.LoadJobConfig()
                job_config.skip_leading_rows = 1
                job_config.source_format = bigquery.SourceFormat.CSV
                table_name = f"{file_type}_{os.path.basename(path)}"
                load_job = client.load_table_from_uri(
                    path, dataset_ref.table(table_name), job_config=job_config
                )
                load_job.result()
                ans[file_type] = [True, table_name]
            except Exception as e:
                ans[file_type] = [False, e]
        return ans

    @staticmethod
    def load_to_amplitude():
        def iterate_by_chunks(iterable, n):
            iterable = iter(iterable)
            count = 0
            group = []
            while True:
                try:
                    group.append(next(iterable))
                    count += 1
                    if count % n == 0:
                        yield group
                        group = []
                except StopIteration:
                    yield group
                    break

        def upload_chunk_to_amplitude(chunk):
            headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*'
            }
            r = requests.post(
                'https://api.amplitude.com/batch', params={},
                headers=headers, json={"api_key": settings.PANDEMITICA_AMPLITUDE_API_KEY, "events": chunk}
            )
            if r.json()['code'] != 200:
                raise Exception("AmlitudeException")
            time.sleep(1)

        def upload_one_table(bq, table_id):
            query_job = bq.query(
                f"""SELECT * EXCEPT(ROW_ID), CONCAT(event_type, "/", ROW_ID)
                    AS insert_id FROM 
                `{settings.PANDEMITICA_GOOGLE_CLOUD_PROJECT}.{settings.PANDEMITICA_GOOGLE_BIGQUERY_DATASET}.{table_id}`"""
            )
            query_job.result()
            destination = query_job.destination
            destination = bq.get_table(destination)
            chunks = iterate_by_chunks(bq.list_rows(destination), 1000)
            for chunk in chunks:
                output_chunk = []
                for row in chunk:
                    line = {"event_properties": {}, "user_properties": {}}
                    for key, value in row.items():
                        if key in ROOT_FIELDS:
                            dict_to_put = line
                        elif key in USER_FIELDS:
                            dict_to_put = line["user_properties"]
                        else:
                            dict_to_put = line["event_properties"]
                        dict_to_put[key] = value
                    output_chunk.append(line)
                upload_chunk_to_amplitude(output_chunk)

        ROOT_FIELDS = ["user_id", "event_type", "time", "insert_id"]
        USER_FIELDS = ["gender", "language", "religion", "marital_status", "ethnicity"]
        client = bigquery.Client.from_service_account_json(settings.PANDEMITICA_GOOGLE_CLOUD_CRED,
                                                           project=settings.PANDEMITICA_GOOGLE_CLOUD_PROJECT)
        dataset = client.get_dataset(settings.PANDEMITICA_GOOGLE_BIGQUERY_DATASET)
        for table in client.list_tables(dataset):
            if table.table_id not in ['UserData']:
                upload_one_table(client, table.table_id)
        return True


class ProfileView(View):
    template_name = 'users/profile.html'

    def __init__(self, *args, **kwargs):
        super(ProfileView, self).__init__(*args, **kwargs)
        self.context = {'error': ''}

    def get(self, request, *args, **kwargs):
        self.context['user'] = request.user
        if request.user.id != self.kwargs['id_user']:
            self.context['error'] = 'Sorry!\nYou can watch only your profile page'
        else:
            self.context['error'] = ''
        return render(request, self.template_name, self.context)


class SignUpView(View):
    form = SignupForm
    template_name = 'load_files/signup.html'

    def __init__(self, *args, **kwargs):
        super(SignUpView, self).__init__(*args, **kwargs)
        self.context = {}

    def get(self, request, *args, **kwargs):
        self.context['form'] = self.form()
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            form.save()
            url = request.POST.get('continue', '/load_files/login/')
            return HttpResponseRedirect(url)
        self.context['form'] = form
        return render(request, self.template_name, self.context)


class LogInView(View):
    form = LoginForm
    template_name = 'load_files/login.html'

    def __init__(self, *args, **kwargs):
        super(LogInView, self).__init__(*args, **kwargs)
        self.context = {'error': ''}

    def get(self, request, *args, **kwargs):
        form = self.form()
        self.context['form'] = form
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            url = request.POST.get('continue', '/')
            return HttpResponseRedirect(url)
        self.context['form'] = self.form()
        self.context['error'] = 'Invalid username/password'
        return render(request, self.template_name, self.context)


def logout_view(request):
    logout(request)
    return redirect(request.GET.get('continue', '/'))