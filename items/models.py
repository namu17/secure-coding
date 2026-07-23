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

    class Status(models.TextChoices):
        AVAILABLE = 'available', '거래 전'
        RESERVED = 'reserved', '거래 중'
        SOLD = 'sold', '거래 완료'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items'
    )
    description = models.TextField()
    price = models.PositiveIntegerField()
    like_count = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=20, choices=Category.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)
    region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name='items'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField('비공개 처리됨', default=False)

    def __str__(self):
        return f'{self.description[:30]} ({self.price}원)'


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(upload_to='items/')

    def __str__(self):
        return f'Image for item #{self.item_id}'


class ItemLike(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_items'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['item', 'user'], name='unique_item_like')
        ]

    def __str__(self):
        return f'{self.user_id} likes item #{self.item_id}'


class Report(models.Model):
    class Reason(models.TextChoices):
        AD = 'ad', '광고성 게시물'
        BAD_PHOTO = 'bad_photo', '부적절한 사진'
        ABUSIVE = 'abusive', '욕설 및 혐오 표현 사용'
        FRAUD = 'fraud', '사기'

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='filed_reports'
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['item', 'reporter'], name='unique_item_report')
        ]

    def __str__(self):
        return f'{self.reporter_id} reported item #{self.item_id} ({self.reason})'
