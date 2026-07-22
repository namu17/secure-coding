from django import forms
from django.forms import inlineformset_factory

from items.models import Item, ItemImage

ItemForm = forms.modelform_factory(
    Item, fields=['description', 'price', 'category', 'region']
)

ItemImageFormSet = inlineformset_factory(
    Item, ItemImage, fields=['image_url'], extra=3, can_delete=False
)
