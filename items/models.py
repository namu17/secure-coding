import io
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from PIL import Image

from regions.models import Region

MIN_ITEM_PRICE = 100
MAX_ITEM_PRICE = 100_000_000
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']


def item_image_upload_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return f'items/{uuid.uuid4().hex}.{ext}'


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
    price = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_ITEM_PRICE), MaxValueValidator(MAX_ITEM_PRICE)]
    )
    like_count = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=20, choices=Category.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)
    region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name='items'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField('비공개 처리됨', default=False)
    pending_review = models.BooleanField('관리자 검토 대기', default=False)

    def __str__(self):
        return f'{self.description[:30]} ({self.price}원)'


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image_url = models.ImageField(
        upload_to=item_image_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS)],
    )

    def __str__(self):
        return f'Image for item #{self.item_id}'

    def save(self, *args, **kwargs):
        if isinstance(self.image_url.file, UploadedFile):
            self._reencode_image()
        super().save(*args, **kwargs)

    def _reencode_image(self):
        """Re-encodes the uploaded file through Pillow so only decoded pixel
        data reaches storage. Strips EXIF/metadata and any trailing bytes a
        polyglot upload might smuggle past the raw ImageField validation.
        """
        self.image_url.file.seek(0)
        with Image.open(self.image_url.file) as img:
            img.load()
            if img.mode == 'RGBA' or 'transparency' in img.info:
                img = img.convert('RGBA')
                out_format, ext = 'PNG', 'png'
            else:
                img = img.convert('RGB')
                out_format, ext = 'JPEG', 'jpg'

            buffer = io.BytesIO()
            img.save(buffer, format=out_format)

        buffer.seek(0)
        self.image_url = ContentFile(buffer.read(), name=f'{uuid.uuid4().hex}.{ext}')


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
