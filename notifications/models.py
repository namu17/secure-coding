from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        CHAT = 'chat', '채팅'
        TRANSFER = 'transfer', '송금'
        REPORT = 'report', '신고'
        PRICE_DROP = 'price_drop', '가격 인하'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    message = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_type_display()}] {self.message}'
