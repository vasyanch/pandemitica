from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy

from .models import User, File


class SignupForm(UserCreationForm):
    username = forms.EmailField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ivan@gmail.com', 'id': 'username'})
    )
    password1 = forms.CharField(
        label=gettext_lazy("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'id': 'password1'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=gettext_lazy("Password confirmation"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'id': 'password2'}),
        strip=False,
        help_text=gettext_lazy("Enter the same password as before, for verification."),
    )


class LoadFileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file']

    def clear_file(self):
        file = self.cleaned_data.get('file')
        # тут надо добавить проверку что файл csv
        # if file is not None:
        #    raise forms.ValidationError('Wrong format of picture')
        return file


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    username = forms.EmailField(widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'ivan@gmail.com',
            'id': 'username'
        }))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'id': 'password',
        }))

"""class ChangeFieldsForm(forms.Form):
    new_email = forms.EmailField(max_length=100)
    new_avatar = forms.ImageField(required=False)

    def clean_new_avatar(self):
        new_avatar = self.cleaned_data.get('new_avatar')
        if new_avatar is not None and'image' not in new_avatar.content_type:
            raise forms.ValidationError('Wrong format of picture')
        return new_avatar

    def save(self):
        return self.cleaned_data


class UserProfileSignupForm(forms.ModelForm):

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar is not None and 'image' not in avatar.content_type:
            raise forms.ValidationError('Wrong format of picture')
        return avatar

    class Meta:
        model = UserProfile
        fields = ['avatar']"""