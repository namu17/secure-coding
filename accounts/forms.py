from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.safestring import mark_safe

from accounts.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'nickname', 'email', 'phone_number', 'region']
        labels = {
            'username': '아이디',
            'email': '이메일',
        }
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'pattern': r'01[0-9]-\d{3,4}-\d{4}',
                'placeholder': '010-1234-5678',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = '비밀번호'
        self.fields['password1'].help_text = mark_safe(
            '- 개인정보 포함 X<br>'
            '- 흔한 비밀번호 X<br>'
            '- 영문, 숫자, 특수문자 포함<br>'
            '- 최소 8자 이상'
        )
        self.fields['password2'].label = '비밀번호 확인'
        self.fields['password2'].help_text = ''


class LoginForm(forms.Form):
    username = forms.CharField(label='아이디')
    password = forms.CharField(label='비밀번호', widget=forms.PasswordInput)


class ReauthForm(forms.Form):
    password = forms.CharField(label='비밀번호', widget=forms.PasswordInput)


ProfileForm = forms.modelform_factory(
    User,
    fields=['nickname', 'email', 'phone_number', 'region'],
    labels={'email': '이메일'},
    widgets={
        'phone_number': forms.TextInput(attrs={
            'pattern': r'01[0-9]-\d{3,4}-\d{4}',
            'placeholder': '010-1234-5678',
        }),
    },
)
