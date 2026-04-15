from django.urls import path

from .views import (
    NearbyPartnerStoresView,
    SavePlayerPartnerStoresView,
    GetPlayerPartnerStoresView,
)

urlpatterns = [
    path("nearby/", NearbyPartnerStoresView.as_view(), name="partner-stores-nearby"),
    path("save/", SavePlayerPartnerStoresView.as_view(), name="partner-stores-save"),
    path(
        "player/<int:player_id>/",
        GetPlayerPartnerStoresView.as_view(),
        name="partner-stores-player",
    ),
    path(
        "player/",
        GetPlayerPartnerStoresView.as_view(),
        name="partner-stores-player-query",
    ),
]
