from django.contrib.auth.models import AbstractUser
from django.db import models

from regions.models import Region


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ADMIN = 'admin', 'Admin'

    phone_number = models.CharField(max_length=20, blank=True)
    nickname = models.CharField(max_length=50, unique=True)
    region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name='users'
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = ['email', 'nickname']

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
