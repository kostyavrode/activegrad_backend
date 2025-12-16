from django.urls import path
from .views import (
    RegisterAPIView, LoginAPIView, CustomLoginView, UpdateClothesAPIView, 
    GetPlayerInfoView, GetPlayerLandmarksView, GetCurrentUserStatsView, GetCurrentUserCoinsView
)


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("update-clothes/", UpdateClothesAPIView.as_view(), name="update-clothes"),
    path("player/<int:player_id>/", GetPlayerInfoView.as_view(), name="get-player-info"),
    path("player/<int:player_id>/landmarks/", GetPlayerLandmarksView.as_view(), name="get-player-landmarks"),
    path("player/stats/", GetCurrentUserStatsView.as_view(), name="get-current-user-stats"),
    path("player/coins/", GetCurrentUserCoinsView.as_view(), name="get-current-user-coins"),
]
