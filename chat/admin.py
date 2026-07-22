from django.contrib import admin

from chat.models import ChatRoom, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'content', 'created_at')
    can_delete = False


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'buyer', 'seller', 'created_at')
    search_fields = ('item__description', 'buyer__nickname', 'seller__nickname')
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'content', 'created_at')
    search_fields = ('content', 'sender__nickname')
