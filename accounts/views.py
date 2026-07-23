import math

import jwt
from django.contrib.auth import authenticate
from django.contrib.auth import logout as session_logout
from django.shortcuts import redirect, render
from django.utils import timezone
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


def suspension_message(user):
    remaining_days = math.ceil((user.suspended_until - timezone.now()).total_seconds() / 86400)
    return f'신고 누적으로 계정이 정지되었습니다. (남은 기간: {remaining_days}일)'


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
            if user is not None and user.is_suspended:
                error = suspension_message(user)
            elif user is not None:
                access_token, refresh_token = issue_tokens(user)
                response = redirect('items:list')
                set_auth_cookies(response, access_token, refresh_token)
                return response
            else:
                error = '아이디 또는 비밀번호가 올바르지 않습니다.'
        return render(request, 'accounts/login.html', {'form': form, 'error': error})


class LogoutView(View):
    def post(self, request):
        response = redirect('accounts:login')
        if request.user.is_authenticated:
            session_logout(request)
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

        if user.is_suspended:
            revoke_refresh_token(payload['jti'])
            return redirect('accounts:login')

        revoke_refresh_token(payload['jti'])
        access_token, new_refresh_token = issue_tokens(user)
        response = redirect(request.META.get('HTTP_REFERER', 'items:list'))
        set_auth_cookies(response, access_token, new_refresh_token)
        return response
