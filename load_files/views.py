import os
import json

from django.shortcuts import render
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
        self.context = {'error': ''}

    def get(self, request, *args, **kwargs):
        self.context['user'] = request.user
        if self.context['user'].is_authenticated:
            self.context['form'] = self.form()
        else:
            self.context['error'] = 'You need authorization to load file'
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            form = self.form(request.user, request.POST)
            if form.is_valid():
                form.save()
                #url = request.POST.get('continue', request.path)
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
        super().__init__(self, *args, **kwargs)
        self.context = {'error': ''}

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            user_files = File.objects.filter(user_id=user.id).all()
            if user_files:
                files_path = {f'{file.file_type.file_type}': file.get_path for file in user_files}
                self.context['load_result'] = self.load_files_to_storage(files_path)
                return render(request, self.template_name_load_result, self.context)
            else:
                self.context['error'] = 'You need load file'
        else:
            self.context['error'] = 'You need authorization to process file'
        return render(request, self.template_name, self.context)

    @staticmethod
    def load_files_to_storage(files_path: dict):
        ans = {key: False for key in files_path.keys()}
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
                ans[file_type] = ''
            except Exception as e:
                ans[file_type] = f'{e}'
        return ans


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