from django.conf import settings
from django.db import models

from items.models import Item


class ChatRoom(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='chat_rooms')
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_as_buyer'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats_as_seller'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('item', 'buyer')

    def __str__(self):
        return f'Chat #{self.id} on item #{self.item_id}'


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender_id}: {self.content[:30]}'
