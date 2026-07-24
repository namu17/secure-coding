import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_user_pending_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(
                blank=True,
                help_text='- 010-1234-5678 형식으로 입력해주세요.',
                max_length=20,
                validators=[
                    django.core.validators.RegexValidator(
                        message='전화번호 형식이 올바르지 않습니다. 예: 010-1234-5678',
                        regex='^01[0-9]-\\d{3,4}-\\d{4}$',
                    )
                ],
                verbose_name='전화번호',
            ),
        ),
    ]
