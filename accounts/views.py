import math
from datetime import timedelta

import jwt
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import logout as session_logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View

from accounts.forms import LoginForm, ProfileForm, ReauthForm, RegisterForm
from accounts.login_throttle import (
    clear_login_failures,
    is_login_locked,
    register_login_failure,
)
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

REAUTH_SESSION_KEY = 'profile_verified_at'
REAUTH_VALID_MINUTES = 10


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
            username = form.cleaned_data['username']
            if is_login_locked(username):
                error = '로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.'
                return render(request, 'accounts/login.html', {'form': form, 'error': error})

            user = authenticate(
                request,
                username=username,
                password=form.cleaned_data['password'],
            )
            if user is not None and user.is_suspended:
                clear_login_failures(username)
                error = suspension_message(user)
            elif user is not None:
                clear_login_failures(username)
                access_token, refresh_token = issue_tokens(user)
                response = redirect('items:list')
                set_auth_cookies(response, access_token, refresh_token)
                return response
            else:
                register_login_failure(username)
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


class ProfileReauthView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/reauth.html', {'form': ReauthForm()})

    def post(self, request):
        form = ReauthForm(request.POST)
        error = None
        if form.is_valid():
            if request.user.check_password(form.cleaned_data['password']):
                request.session[REAUTH_SESSION_KEY] = timezone.now().isoformat()
                return redirect('accounts:profile')
            error = '비밀번호가 올바르지 않습니다.'
        return render(request, 'accounts/reauth.html', {'form': form, 'error': error})


class ProfileReauthRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        verified_at = request.session.get(REAUTH_SESSION_KEY)
        parsed = parse_datetime(verified_at) if verified_at else None
        if not parsed or timezone.now() - parsed > timedelta(minutes=REAUTH_VALID_MINUTES):
            return redirect('accounts:profile_reauth')
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, ProfileReauthRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/profile.html', self._context(request))

    def post(self, request):
        form_type = request.POST.get('form_type')
        if form_type == 'password':
            return self._handle_password_change(request)
        return self._handle_info_update(request)

    def _context(self, request, **extra):
        from items.models import Item

        context = {
            'profile_form': ProfileForm(instance=request.user),
            'password_form': PasswordChangeForm(request.user),
            'my_items': Item.objects.filter(seller=request.user).order_by('-created_at'),
        }
        context.update(extra)
        return context

    def _handle_info_update(self, request):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '내 정보가 수정되었습니다.')
            return redirect('accounts:profile')
        return render(request, 'accounts/profile.html', self._context(request, profile_form=form))

    def _handle_password_change(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()

            response = redirect('accounts:login')
            access_token = request.COOKIES.get(ACCESS_COOKIE)
            if access_token:
                try:
                    blacklist_token(decode_token(access_token))
                except jwt.InvalidTokenError:
                    pass
            refresh_token = request.COOKIES.get(REFRESH_COOKIE)
            if refresh_token:
                try:
                    payload = jwt.decode(
                        refresh_token, options={'verify_signature': False}, algorithms=['HS256']
                    )
                    revoke_refresh_token(payload['jti'])
                except jwt.InvalidTokenError:
                    pass
            clear_auth_cookies(response)
            del request.session[REAUTH_SESSION_KEY]
            messages.success(request, '비밀번호가 변경되었습니다. 다시 로그인해주세요.')
            return response
        return render(request, 'accounts/profile.html', self._context(request, password_form=form))


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
