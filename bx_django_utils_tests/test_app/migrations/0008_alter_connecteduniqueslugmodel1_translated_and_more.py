# Generated by Django 4.1.8 on 2023-04-12 12:56

from django.db import migrations

import bx_django_utils.translation


class Migration(migrations.Migration):
    dependencies = [
        ("test_app", "0007_connecteduniqueslugmodel1_connecteduniqueslugmodel2"),
    ]

    operations = [
        migrations.AlterField(
            model_name="connecteduniqueslugmodel1",
            name="translated",
            field=bx_django_utils.translation.TranslationField(
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                )
            ),
        ),
        migrations.AlterField(
            model_name="connecteduniqueslugmodel1",
            name="translated_slug",
            field=bx_django_utils.translation.TranslationSlugField(
                additional_uniqueness=(
                    {
                        "app_label": "test_app",
                        "field_name": "translated_slug",
                        "model_name": "ConnectedUniqueSlugModel2",
                    },
                ),
                blank=True,
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                ),
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="connecteduniqueslugmodel2",
            name="translated",
            field=bx_django_utils.translation.TranslationField(
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                )
            ),
        ),
        migrations.AlterField(
            model_name="connecteduniqueslugmodel2",
            name="translated_slug",
            field=bx_django_utils.translation.TranslationSlugField(
                additional_uniqueness=(
                    {
                        "app_label": "test_app",
                        "field_name": "translated_slug",
                        "model_name": "ConnectedUniqueSlugModel1",
                    },
                ),
                blank=True,
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                ),
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="nonuniquetranslatedslugtestmodel",
            name="translated",
            field=bx_django_utils.translation.TranslationField(
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                )
            ),
        ),
        migrations.AlterField(
            model_name="nonuniquetranslatedslugtestmodel",
            name="translated_slug",
            field=bx_django_utils.translation.TranslationSlugField(
                additional_uniqueness=None,
                blank=True,
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                ),
                unique=False,
            ),
        ),
        migrations.AlterField(
            model_name="translatedmodel",
            name="translated",
            field=bx_django_utils.translation.TranslationField(
                languages=(("de-de", "de-de"), ("en-us", "en-us"), ("es", "es"))
            ),
        ),
        migrations.AlterField(
            model_name="translatedmodel",
            name="translated_multiline",
            field=bx_django_utils.translation.TranslationField(
                blank=True,
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                ),
            ),
        ),
        migrations.AlterField(
            model_name="translatedslugtestmodel",
            name="translated",
            field=bx_django_utils.translation.TranslationField(
                languages=(
                    ("de-de", "German"),
                    ("en-us", "US-English"),
                    ("es", "Spanish"),
                )
            ),
        ),
        migrations.AlterField(
            model_name="translatedslugtestmodel",
            name="translated_slug",
            field=bx_django_utils.translation.TranslationSlugField(
                additional_uniqueness=None,
                blank=True,
                languages=(("de-de", "de-de"), ("en-us", "en-us"), ("es", "es")),
                unique=True,
            ),
        ),
    ]