# Generated by Django 5.0.7 on 2024-08-09 20:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0016_rename_keyword_recommender_system_bill_keyword_recommenation_system'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='keyword_recommenation_system',
            new_name='keyword_recommendation_system',
        ),
    ]
