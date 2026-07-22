from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'nickname', 'email', 'phone_number', 'region']


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
