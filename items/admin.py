from django.contrib import admin

from items.models import Item, ItemImage, Report


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'description', 'price', 'category', 'seller', 'region',
        'is_hidden', 'pending_review', 'created_at',
    )
    list_filter = ('category', 'region', 'is_hidden', 'pending_review')
    list_editable = ('is_hidden',)
    search_fields = ('description', 'seller__username')
    inlines = [ItemImageInline]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'reporter', 'reason', 'created_at')
    list_filter = ('reason',)
    search_fields = ('item__description', 'reporter__username')
