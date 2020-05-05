from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy

from .models import File


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
        fields = ['file', 'file_type', 'user']


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
