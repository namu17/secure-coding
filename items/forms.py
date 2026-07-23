import re

from django import forms
from django.forms import inlineformset_factory

from items.models import Item, ItemImage

BANNED_DESCRIPTION_PATTERNS = [
    re.compile(r'https?://\S+', re.IGNORECASE),
    re.compile(r't\.me/\S+', re.IGNORECASE),
    re.compile(r'open\.kakao\.com/\S+', re.IGNORECASE),
    re.compile(r'텔레그램|카카오\s*오픈\s*채팅|카톡\s*(아이디|id)', re.IGNORECASE),
    re.compile(r'01[016789]-?\d{3,4}-?\d{4}'),
]


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['description', 'price', 'category', 'region']

    def clean_description(self):
        description = self.cleaned_data['description']
        for pattern in BANNED_DESCRIPTION_PATTERNS:
            if pattern.search(description):
                raise forms.ValidationError(
                    '상품 설명에 외부 링크, 메신저 아이디, 전화번호는 포함할 수 없습니다. '
                    '거래는 채팅 기능을 이용해주세요.'
                )
        return description


ItemImageFormSet = inlineformset_factory(
    Item, ItemImage, fields=['image_url'], extra=3, can_delete=True
)
