import re

from django.core.exceptions import ValidationError


class ComplexPasswordValidator:
    """Requires at least one letter, one digit, and one special character."""

    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError('비밀번호는 영문을 포함해야 합니다.', code='password_no_letter')
        if not re.search(r'\d', password):
            raise ValidationError('비밀번호는 숫자를 포함해야 합니다.', code='password_no_digit')
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError(
                '비밀번호는 특수문자를 포함해야 합니다.', code='password_no_special'
            )

    def get_help_text(self):
        return '영문, 숫자, 특수문자를 모두 포함해야 합니다.'
