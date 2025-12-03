from django.urls import path
from .views import SavePlayerLandmarksView, GetPlayerLandmarksView

urlpatterns = [
    path('save/', SavePlayerLandmarksView.as_view(), name='save-player-landmarks'),
    path('player/<int:player_id>/', GetPlayerLandmarksView.as_view(), name='get-player-landmarks'),
    path('player/', GetPlayerLandmarksView.as_view(), name='get-player-landmarks-query'),
]

