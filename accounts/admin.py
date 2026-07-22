from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'nickname', 'email', 'role', 'region', 'is_staff')
    list_filter = ('role', 'region')
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('nickname', 'phone_number', 'region', 'role')}),
    )
