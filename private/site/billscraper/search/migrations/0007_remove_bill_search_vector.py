# Generated by Django 4.2.13 on 2024-07-16 18:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0006_rename_collection_bill_content_collection'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bill',
            name='search_vector',
        ),
    ]
