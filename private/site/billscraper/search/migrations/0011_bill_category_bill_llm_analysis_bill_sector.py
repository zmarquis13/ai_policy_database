# Generated by Django 4.2.13 on 2024-08-02 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0010_bill_last_action_bill_last_action_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='category',
            field=models.CharField(default='N/A'),
        ),
        migrations.AddField(
            model_name='bill',
            name='llm_analysis',
            field=models.CharField(default='N/A'),
        ),
        migrations.AddField(
            model_name='bill',
            name='sector',
            field=models.CharField(default='N/A'),
        ),
    ]
