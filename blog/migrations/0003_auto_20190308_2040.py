# Generated by Django 2.1.7 on 2019-03-08 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_auto_20190307_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='allow_comments',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='article',
            name='show_comments_publically',
            field=models.BooleanField(default=True),
        ),
    ]
