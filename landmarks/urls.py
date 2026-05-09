from django.urls import path
from .views import (
    SavePlayerLandmarksView, GetPlayerLandmarksView, TestLandmarksView,
    CaptureLandmarkView, GetLandmarkCaptureView, CollectCaptureRewardsView,
)

urlpatterns = [
    path('test/', TestLandmarksView.as_view(), name='test-landmarks'),
    path('save/', SavePlayerLandmarksView.as_view(), name='save-player-landmarks'),
    path('player/<int:player_id>/', GetPlayerLandmarksView.as_view(), name='get-player-landmarks'),
    path('player/', GetPlayerLandmarksView.as_view(), name='get-player-landmarks-query'),

    # Landmark capture endpoints
    path('capture/', CaptureLandmarkView.as_view(), name='capture-landmark'),
    path('collect-rewards/', CollectCaptureRewardsView.as_view(), name='collect-capture-rewards'),
    path('<str:external_id>/capture/', GetLandmarkCaptureView.as_view(), name='get-landmark-capture'),
]

