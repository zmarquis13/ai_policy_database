# Generated by Django 4.2.13 on 2024-08-08 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0014_rename_social_impact_bill_societal_impact'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bill',
            name='keyword_automated_decision',
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_automated',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_autonomous_vehicle',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_chatbot',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_deep_learning',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_deepfake',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_foundation_model',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_large_language_model',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_recommender_system',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='bill',
            name='keyword_synthetic_media',
            field=models.IntegerField(default=0),
        ),
    ]
