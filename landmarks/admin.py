from django.contrib import admin
from .models import PlayerLandmarkObservation


@admin.register(PlayerLandmarkObservation)
class PlayerLandmarkObservationAdmin(admin.ModelAdmin):
    list_display = ("player", "external_id", "observed_at")
    list_filter = ("observed_at",)
    search_fields = ("player__username", "external_id")
    readonly_fields = ("observed_at",)
    list_per_page = 50
