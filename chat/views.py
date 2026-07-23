from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from chat.models import ChatRoom
from items.models import Item


class StartChatView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(Item, pk=item_id)
        if item.seller_id == request.user.id:
            raise PermissionDenied('본인 상품에는 채팅을 걸 수 없습니다.')

        room, _ = ChatRoom.objects.get_or_create(
            item=item, buyer=request.user, defaults={'seller': item.seller}
        )
        return redirect('chat:room_detail', pk=room.pk)


class ChatRoomListView(LoginRequiredMixin, ListView):
    template_name = 'chat/room_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        user = self.request.user
        rooms = ChatRoom.objects.filter(Q(buyer=user) | Q(seller=user)).select_related(
            'item', 'buyer', 'seller'
        )
        for room in rooms:
            room.partner = room.seller if room.buyer_id == user.id else room.buyer
        return rooms


class ChatRoomDetailView(LoginRequiredMixin, DetailView):
    model = ChatRoom
    template_name = 'chat/room_detail.html'
    context_object_name = 'room'

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.select_related('item', 'buyer', 'seller').filter(
            Q(buyer=user) | Q(seller=user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message_history'] = self.object.messages.select_related('sender')
        user = self.request.user
        context['recipient'] = (
            self.object.seller if self.object.buyer_id == user.id else self.object.buyer
        )
        return context
