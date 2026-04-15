from django.contrib import admin
from .models import PartnerStoreTag, PartnerStore, PlayerPartnerStoreObservation


@admin.register(PartnerStoreTag)
class PartnerStoreTagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(PartnerStore)
class PartnerStoreAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active",
        "latitude",
        "longitude",
        "created_at",
    )
    list_filter = ("is_active", "tags")
    search_fields = ("name", "address")
    filter_horizontal = ("tags",)
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "name",
                    "address",
                    "image_url",
                    "is_active",
                    "tags",
                )
            },
        ),
        ("Координаты", {"fields": ("latitude", "longitude")}),
        ("Служебное", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(PlayerPartnerStoreObservation)
class PlayerPartnerStoreObservationAdmin(admin.ModelAdmin):
    list_display = ("id", "player", "partner_store", "observed_at")
    list_filter = ("observed_at",)
    search_fields = ("player__username", "partner_store__name")
    readonly_fields = ("observed_at",)
    autocomplete_fields = ("player", "partner_store")
