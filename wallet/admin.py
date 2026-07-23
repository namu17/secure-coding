from django.contrib import admin

from wallet.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'from_user', 'to_user', 'amount', 'room', 'created_at')
    list_filter = ('type',)
    search_fields = ('from_user__username', 'to_user__username')
    readonly_fields = ('type', 'from_user', 'to_user', 'amount', 'room', 'created_at')

    def has_add_permission(self, request):
        return False
