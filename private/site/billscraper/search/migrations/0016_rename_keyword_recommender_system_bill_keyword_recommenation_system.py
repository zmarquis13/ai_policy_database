# Generated by Django 4.2.13 on 2024-08-09 17:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0015_remove_bill_keyword_automated_decision_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='keyword_recommender_system',
            new_name='keyword_recommenation_system',
        ),
    ]
