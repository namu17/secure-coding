from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'nickname', 'email', 'role', 'region', 'is_staff', 'suspended_until',
        'pending_review', 'balance',
    )
    list_filter = ('role', 'region', 'pending_review')
    fieldsets = UserAdmin.fieldsets + (
        (
            '추가 정보',
            {
                'fields': (
                    'nickname', 'phone_number', 'region', 'role',
                    'pending_review', 'suspended_until', 'balance',
                )
            },
        ),
    )
