import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q

from chat.models import ChatRoom, Message
from notifications.services import notify


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.group_name = f'chat_{self.room_id}'
        user = self.scope['user']

        if not user.is_authenticated or not await self._is_participant(user):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
            return

        content = data.get('message', '').strip()
        if not content:
            return

        user = self.scope['user']
        message = await self._save_message(user, content)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.message',
                'message': message.content,
                'sender_id': message.sender_id,
                'sender_nickname': user.nickname,
                'created_at': message.created_at.isoformat(),
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def _is_participant(self, user):
        return ChatRoom.objects.filter(Q(buyer=user) | Q(seller=user), pk=self.room_id).exists()

    @database_sync_to_async
    def _save_message(self, user, content):
        room = ChatRoom.objects.select_related('buyer', 'seller').get(pk=self.room_id)
        message = Message.objects.create(room=room, sender=user, content=content)
        partner = room.seller if room.buyer_id == user.id else room.buyer
        notify(
            partner,
            'chat',
            f'{user.nickname}: {content[:30]}',
            f'/chats/{room.id}/',
        )
        return message
