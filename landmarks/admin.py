from django.contrib import admin
from .models import PlayerLandmarkObservation, LandmarkCapture


@admin.register(PlayerLandmarkObservation)
class PlayerLandmarkObservationAdmin(admin.ModelAdmin):
    list_display = ("player", "external_id", "observed_at")
    list_filter = ("observed_at",)
    search_fields = ("player__username", "external_id")
    readonly_fields = ("observed_at",)
    list_per_page = 50


@admin.register(LandmarkCapture)
class LandmarkCaptureAdmin(admin.ModelAdmin):
    list_display = ("id", "external_id", "captured_by", "clan", "captured_at")
    list_filter = ("captured_at", "clan")
    search_fields = ("external_id", "captured_by__username", "clan__name")
    readonly_fields = ("captured_at",)
    list_per_page = 50
