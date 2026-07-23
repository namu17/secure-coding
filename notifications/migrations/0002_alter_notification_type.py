from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(
                choices=[
                    ('chat', '채팅'),
                    ('transfer', '송금'),
                    ('report', '신고'),
                    ('price_drop', '가격 인하'),
                ],
                max_length=10,
            ),
        ),
    ]
