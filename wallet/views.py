from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.models import User
from chat.models import ChatRoom, Message
from notifications.services import notify
from wallet.models import Transaction


def _parse_amount(raw_value):
    try:
        amount = int(raw_value)
    except (TypeError, ValueError):
        return None
    return amount if amount > 0 else None


class ChargeView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'wallet/charge_form.html')

    def post(self, request):
        amount = _parse_amount(request.POST.get('amount'))
        if amount is None:
            messages.error(request, '충전할 금액을 올바르게 입력해주세요.')
            return render(request, 'wallet/charge_form.html')

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            user.balance += amount
            user.save(update_fields=['balance'])
            Transaction.objects.create(
                type=Transaction.Type.CHARGE, from_user=None, to_user=user, amount=amount
            )

        messages.success(request, f'{amount:,}원이 충전되었습니다.')
        return redirect('items:list')


class TransferView(LoginRequiredMixin, View):
    def post(self, request, room_id):
        room = get_object_or_404(
            ChatRoom.objects.select_related('buyer', 'seller'),
            Q(buyer=request.user) | Q(seller=request.user),
            pk=room_id,
        )
        recipient = room.seller if room.buyer_id == request.user.id else room.buyer

        amount = _parse_amount(request.POST.get('amount'))
        if amount is None:
            messages.error(request, '송금할 금액을 올바르게 입력해주세요.')
            return redirect('chat:room_detail', pk=room.pk)

        with transaction.atomic():
            locked_users = User.objects.select_for_update().filter(
                pk__in=sorted([request.user.pk, recipient.pk])
            )
            users_by_id = {user.pk: user for user in locked_users}
            sender = users_by_id[request.user.pk]
            recipient = users_by_id[recipient.pk]

            if sender.balance < amount:
                messages.error(request, '잔액이 부족합니다.')
                return redirect('chat:room_detail', pk=room.pk)

            sender.balance -= amount
            recipient.balance += amount
            sender.save(update_fields=['balance'])
            recipient.save(update_fields=['balance'])
            Transaction.objects.create(
                type=Transaction.Type.TRANSFER,
                from_user=sender,
                to_user=recipient,
                amount=amount,
                room=room,
            )

        chat_message = Message.objects.create(
            room=room, sender=sender, content=f'송금 완료: {amount:,}원'
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room.id}',
            {
                'type': 'chat.message',
                'message': chat_message.content,
                'sender_id': chat_message.sender_id,
                'sender_nickname': sender.nickname,
                'created_at': chat_message.created_at.isoformat(),
            },
        )

        notify(
            recipient,
            'transfer',
            f'{sender.nickname}님이 {amount:,}원을 보냈습니다.',
            f'/chats/{room.id}/',
        )

        messages.success(request, f'{recipient.nickname}님에게 {amount:,}원을 송금했습니다.')
        return redirect('chat:room_detail', pk=room.pk)
