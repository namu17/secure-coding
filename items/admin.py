from django.contrib import admin

from items.models import Item, ItemImage


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'price', 'category', 'seller', 'region', 'created_at')
    list_filter = ('category', 'region')
    search_fields = ('description', 'seller__username')
    inlines = [ItemImageInline]
