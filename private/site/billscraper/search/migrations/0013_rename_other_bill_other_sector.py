# Generated by Django 4.2.13 on 2024-08-06 20:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0012_remove_bill_category_remove_bill_llm_analysis_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='other',
            new_name='other_sector',
        ),
    ]
