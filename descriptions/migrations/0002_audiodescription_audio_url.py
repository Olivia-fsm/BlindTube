# Generated by Django 5.2.3 on 2025-06-22 01:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("descriptions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="audiodescription",
            name="audio_url",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
