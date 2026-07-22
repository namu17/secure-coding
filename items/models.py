from django.conf import settings
from django.db import models

from regions.models import Region


class Item(models.Model):
    class Category(models.TextChoices):
        DIGITAL = 'digital', '디지털기기'
        FURNITURE = 'furniture', '가구/인테리어'
        CLOTHING = 'clothing', '의류'
        BOOKS = 'books', '도서'
        ETC = 'etc', '기타'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items'
    )
    description = models.TextField()
    price = models.PositiveIntegerField()
    like_count = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=20, choices=Category.choices)
    region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name='items'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.description[:30]} ({self.price}원)'


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='items/')

    def __str__(self):
        return f'Image for item #{self.item_id}'
