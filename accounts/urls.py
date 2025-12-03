from django.urls import path
from .views import RegisterAPIView, LoginAPIView, CustomLoginView, UpdateClothesAPIView, GetPlayerInfoView


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("update-clothes/", UpdateClothesAPIView.as_view(), name="update-clothes"),
    path("player/<int:player_id>/", GetPlayerInfoView.as_view(), name="get-player-info"),
]
