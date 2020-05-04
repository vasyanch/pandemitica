import os
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class FileType(models.Model):
    file_type = models.CharField(max_length=400, unique=True)


def file_directory_path(instance, filename):
    return os.path.join(f'file_type_{instance.file_type.file_type}', filename)


class File(models.Model):
    file = models.FileField(verbose_name='data_file', upload_to=file_directory_path, blank=False, null=False)
    filename = models.CharField(max_length=400, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='files')
    file_type = models.ForeignKey('FileType', on_delete=models.SET_NULL, null=True, related_name='files')

    def get_path(self):
        media_path = f'media/file_type_{self.file_type.file_type}/{self.filename}'  # разобраться как грузить файлы
        return os.path.join(settings.BASE_DIR, media_path)









"""class QuestionManager(models.Manager):
    def new(self):
        return self.order_by('-added_at', '-rating')

    def popular(self):
        return self.order_by('-rating', '-added_at')


class Question(Vote, models.Model):
    title = models.CharField(verbose_name='title', max_length=255)
    text = models.TextField()
    author = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    added_at = models.DateTimeField(blank=True, auto_now_add=True)
    rating = models.IntegerField(default=0)
    tags = models.ManyToManyField(Tag, related_name='questions')
    correct_answer = models.OneToOneField('Answer', on_delete=models.SET_NULL, blank=True, null=True,
                                          related_name='correct_answer')
    objects = QuestionManager()

    def __str__(self):
        return self.text

    def get_url(self):
        return reverse('qa:question', args=[self.id])

    def save(self, tags_str=[], *args, **kwargs):
        super(Question, self).save(*args, **kwargs)
        tags_list = []
        for t in tags_str:
            tag, created = Tag.objects.get_or_create(text=t)
            tags_list.append(tag)
        self.tags.add(*tags_list)

    def get_tags(self):
        return self.tags.all()

    def get_answers(self):
        return self.answer_set.order_by('-rating', 'added_at')

    def get_date(self):
        return self.added_at.strftime("%d.%m.%Y")

    def vote(self, rating, user):
        if super(Question, self).vote(rating):
            user.userprofile.vote_question(question_id=self.id,
                                           rating=rating,
                                           question_title=self.title)

    def cancel_vote(self, rating):
        self.rating = self.rating - rating
        self.save()


class Answer(Vote, models.Model):
    text = models.TextField()
    added_at = models.DateTimeField(blank=True, auto_now_add=True)
    rating = models.IntegerField(default=0)
    author = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, null=False, on_delete=models.CASCADE)

    def __str__(self):
        return self.text

    def get_date(self):
        return self.added_at.strftime("%d.%m.%Y")

    def is_correct(self):
        if self.question.correct_answer_id == self.id:
            return True
        return False

    def vote(self, rating, user):
        if super(Answer, self).vote(rating):
            user.userprofile.vote_answer(answer_id=self.id,
                                         rating=rating,
                                         question_title=self.question.title,
                                         question_id=self.question.id)

    def cancel_vote(self, rating):
        self.rating = self.rating - rating
        self.save()"""