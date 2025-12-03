from django.contrib import admin
from .models import Landmark, PlayerLandmarkObservation


@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "external_id")
    search_fields = ("name", "external_id")


@admin.register(PlayerLandmarkObservation)
class PlayerLandmarkObservationAdmin(admin.ModelAdmin):
    list_display = ("player", "landmark", "observed_at")
    list_filter = ("observed_at",)
    search_fields = ("player__username", "landmark__name")
    readonly_fields = ("observed_at",)
