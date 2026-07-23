from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe

from regions.models import Region


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ADMIN = 'admin', 'Admin'

    username = models.CharField(
        '아이디',
        max_length=10,
        unique=True,
        help_text=mark_safe(
            '- 10자 이하<br>'
            '- 영문, 숫자와 @/./+/-/_ 만 사용 가능'
        ),
        validators=[ASCIIUsernameValidator()],
        error_messages={'unique': '이미 사용 중인 아이디입니다.'},
    )
    phone_number = models.CharField('전화번호', max_length=20, blank=True)
    nickname = models.CharField('닉네임', max_length=50, unique=True)
    region = models.ForeignKey(
        Region,
        verbose_name='지역',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    created_at = models.DateTimeField(auto_now_add=True)
    suspended_until = models.DateTimeField('정지 만료 시각', null=True, blank=True)
    balance = models.PositiveIntegerField('보유 머니', default=0)

    REQUIRED_FIELDS = ['email', 'nickname']

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=0), name='balance_non_negative'
            )
        ]

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def is_suspended(self):
        return bool(self.suspended_until and self.suspended_until > timezone.now())

    def __str__(self):
        return self.username
