# Generated by Django 5.1.2 on 2024-11-26 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feature_flags", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="featureflagmodel",
            name="cache_key",
            field=models.CharField(
                help_text="FeatureFlagModel.cache_key.help_text",
                max_length=255,
                primary_key=True,
                serialize=False,
                verbose_name="FeatureFlagModel.cache_key.verbose_name",
            ),
        ),
    ]