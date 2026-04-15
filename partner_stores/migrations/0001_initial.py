# Generated manually for partner_stores app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PartnerStoreTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="Тег"),
                ),
            ],
            options={
                "verbose_name": "Тег магазина",
                "verbose_name_plural": "Теги магазинов",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="PartnerStore",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        decimal_places=6, max_digits=9, verbose_name="Широта"
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        decimal_places=6, max_digits=9, verbose_name="Долгота"
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="Название")),
                ("address", models.CharField(max_length=500, verbose_name="Адрес")),
                (
                    "image_url",
                    models.URLField(
                        blank=True,
                        max_length=500,
                        null=True,
                        verbose_name="URL картинки",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Показывать в API и разрешать отметки",
                        verbose_name="Активен",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True,
                        related_name="stores",
                        to="partner_stores.partnerstoretag",
                        verbose_name="Теги",
                    ),
                ),
            ],
            options={
                "verbose_name": "Магазин партнёра",
                "verbose_name_plural": "Магазины партнёров",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="PlayerPartnerStoreObservation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("observed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "partner_store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="player_observations",
                        to="partner_stores.partnerstore",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="partner_store_observations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Отметка у магазина партнёра",
                "verbose_name_plural": "Отметки у магазинов партнёров",
                "ordering": ["-observed_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="playerpartnerstoreobservation",
            constraint=models.UniqueConstraint(
                fields=("player", "partner_store"),
                name="unique_player_partner_store_observation",
            ),
        ),
        migrations.AddIndex(
            model_name="playerpartnerstoreobservation",
            index=models.Index(
                fields=["player", "partner_store"],
                name="partner_sto_player__idx",
            ),
        ),
        migrations.AddIndex(
            model_name="partnerstore",
            index=models.Index(
                fields=["is_active", "latitude", "longitude"],
                name="partner_sto_is_act_idx",
            ),
        ),
    ]
