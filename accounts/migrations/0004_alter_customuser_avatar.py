# Generated by Django 5.1.7 on 2025-04-27 17:10

import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_customuser_name_alter_customuser_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=models.FileField(blank=True, default='accounts/avatars/default.png', null=True, upload_to=accounts.models.user_avatar_path),
        ),
    ]
