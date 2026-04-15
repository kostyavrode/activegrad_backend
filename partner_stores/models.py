from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PartnerStoreTag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Тег")

    class Meta:
        verbose_name = "Тег магазина"
        verbose_name_plural = "Теги магазинов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PartnerStore(models.Model):
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Широта"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, verbose_name="Долгота"
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    address = models.CharField(max_length=500, verbose_name="Адрес")
    image_url = models.URLField(
        max_length=500, blank=True, null=True, verbose_name="URL картинки"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Показывать в API и разрешать отметки",
    )
    tags = models.ManyToManyField(
        PartnerStoreTag,
        blank=True,
        related_name="stores",
        verbose_name="Теги",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Магазин партнёра"
        verbose_name_plural = "Магазины партнёров"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "latitude", "longitude"]),
        ]

    def __str__(self):
        return self.name


class PlayerPartnerStoreObservation(models.Model):
    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="partner_store_observations",
    )
    partner_store = models.ForeignKey(
        PartnerStore,
        on_delete=models.CASCADE,
        related_name="player_observations",
    )
    observed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отметка у магазина партнёра"
        verbose_name_plural = "Отметки у магазинов партнёров"
        ordering = ["-observed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["player", "partner_store"],
                name="unique_player_partner_store_observation",
            )
        ]
        indexes = [
            models.Index(fields=["player", "partner_store"]),
        ]

    def __str__(self):
        return f"{self.player.username} @ {self.partner_store.name}"
