from django.urls import path
from .views import (
    CreateClanView, JoinClanView, LeaveClanView, SearchClansView, TopClansView
)

urlpatterns = [
    path('create/', CreateClanView.as_view(), name='create-clan'),
    path('join/', JoinClanView.as_view(), name='join-clan'),
    path('leave/', LeaveClanView.as_view(), name='leave-clan'),
    path('search/', SearchClansView.as_view(), name='search-clans'),
    path('top/', TopClansView.as_view(), name='top-clans'),
]

