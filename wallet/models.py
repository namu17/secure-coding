from django.conf import settings
from django.db import models

from chat.models import ChatRoom


class Transaction(models.Model):
    class Type(models.TextChoices):
        CHARGE = 'charge', '충전'
        TRANSFER = 'transfer', '송금'

    type = models.CharField(max_length=10, choices=Type.choices)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sent_transactions',
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transactions'
    )
    amount = models.PositiveIntegerField()
    room = models.ForeignKey(
        ChatRoom, null=True, blank=True, on_delete=models.SET_NULL, related_name='transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_type_display()} {self.amount}원 ({self.from_user_id} -> {self.to_user_id})'
