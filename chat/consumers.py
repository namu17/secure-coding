import json
import re

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q

from chat.models import ChatRoom, Message
from common.redis_client import get_redis_client
from notifications.services import notify

MAX_MESSAGE_LENGTH = 2000
MESSAGE_RATE_LIMIT = 10
MESSAGE_RATE_WINDOW_SECONDS = 10

BANNED_CONTENT_PATTERNS = [
    re.compile(r'https?://\S+', re.IGNORECASE),
    re.compile(r't\.me/\S+', re.IGNORECASE),
    re.compile(r'open\.kakao\.com/\S+', re.IGNORECASE),
    re.compile(r'텔레그램|카카오\s*오픈\s*채팅|카톡\s*(아이디|id)', re.IGNORECASE),
    re.compile(r'01[016789]-?\d{3,4}-?\d{4}'),
]


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
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return
        if not isinstance(data, dict):
            return

        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
            return

        content = data.get('message')
        if not isinstance(content, str):
            return
        content = content.strip()
        if not content or len(content) > MAX_MESSAGE_LENGTH:
            return

        user = self.scope['user']
        if await self._is_rate_limited(user):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'detail': '메시지를 너무 빠르게 보내고 있습니다. 잠시 후 다시 시도해주세요.',
            }))
            return

        if any(pattern.search(content) for pattern in BANNED_CONTENT_PATTERNS):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'detail': (
                    '외부 링크, 메신저 아이디, 전화번호가 포함된 메시지는 보낼 수 없습니다. '
                    '사기 피해 예방을 위해 거래는 채팅과 앱 내 기능만 이용해주세요.'
                ),
            }))
            return

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
    def _is_rate_limited(self, user):
        redis_client = get_redis_client()
        key = f'chat_message_rate:{user.id}'
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, MESSAGE_RATE_WINDOW_SECONDS)
        return count > MESSAGE_RATE_LIMIT

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
