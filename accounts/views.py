import jwt
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render
from django.views import View

from accounts.forms import LoginForm, RegisterForm
from accounts.jwt_utils import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    blacklist_token,
    clear_auth_cookies,
    decode_token,
    is_refresh_token_valid,
    issue_tokens,
    revoke_refresh_token,
    set_auth_cookies,
)
from accounts.models import User


class RegisterView(View):
    def get(self, request):
        return render(request, 'accounts/register.html', {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:login')
        return render(request, 'accounts/register.html', {'form': form})


class LoginView(View):
    def get(self, request):
        return render(request, 'accounts/login.html', {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        error = None
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                access_token, refresh_token = issue_tokens(user)
                response = redirect('items:list')
                set_auth_cookies(response, access_token, refresh_token)
                return response
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'
        return render(request, 'accounts/login.html', {'form': form, 'error': error})


class LogoutView(View):
    def post(self, request):
        response = redirect('accounts:login')
        access_token = request.COOKIES.get(ACCESS_COOKIE)
        if access_token:
            try:
                payload = decode_token(access_token)
                blacklist_token(payload)
            except jwt.InvalidTokenError:
                pass
        refresh_token = request.COOKIES.get(REFRESH_COOKIE)
        if refresh_token:
            try:
                payload = jwt.decode(
                    refresh_token,
                    options={'verify_signature': False},
                    algorithms=['HS256'],
                )
                revoke_refresh_token(payload['jti'])
            except jwt.InvalidTokenError:
                pass
        clear_auth_cookies(response)
        return response


class TokenRefreshView(View):
    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE)
        if not refresh_token:
            return redirect('accounts:login')
        try:
            payload = decode_token(refresh_token)
        except jwt.InvalidTokenError:
            return redirect('accounts:login')

        if payload.get('type') != 'refresh' or not is_refresh_token_valid(payload['jti']):
            return redirect('accounts:login')

        try:
            user = User.objects.get(pk=payload['user_id'])
        except User.DoesNotExist:
            return redirect('accounts:login')

        revoke_refresh_token(payload['jti'])
        access_token, new_refresh_token = issue_tokens(user)
        response = redirect(request.META.get('HTTP_REFERER', 'items:list'))
        set_auth_cookies(response, access_token, new_refresh_token)
        return response
