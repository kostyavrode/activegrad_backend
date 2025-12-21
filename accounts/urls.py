from django.urls import path
from .views import (
    RegisterAPIView, LoginAPIView, CustomLoginView, UpdateClothesAPIView, 
    GetPlayerInfoView, GetPlayerLandmarksView, GetCurrentUserStatsView, GetCurrentUserCoinsView,
    SendFriendRequestView, AcceptFriendRequestView, RejectFriendRequestView,
    GetFriendsListView, GetPendingFriendRequestsView, GetSentFriendRequestsView, RemoveFriendView
)


urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("update-clothes/", UpdateClothesAPIView.as_view(), name="update-clothes"),
    path("player/<int:player_id>/", GetPlayerInfoView.as_view(), name="get-player-info"),
    path("player/<int:player_id>/landmarks/", GetPlayerLandmarksView.as_view(), name="get-player-landmarks"),
    path("player/stats/", GetCurrentUserStatsView.as_view(), name="get-current-user-stats"),
    path("player/coins/", GetCurrentUserCoinsView.as_view(), name="get-current-user-coins"),
    
    # Friend system endpoints
    path("friends/", GetFriendsListView.as_view(), name="get-friends-list"),
    path("friends/requests/send/", SendFriendRequestView.as_view(), name="send-friend-request"),
    path("friends/requests/pending/", GetPendingFriendRequestsView.as_view(), name="get-pending-friend-requests"),
    path("friends/requests/sent/", GetSentFriendRequestsView.as_view(), name="get-sent-friend-requests"),
    path("friends/requests/<int:request_id>/accept/", AcceptFriendRequestView.as_view(), name="accept-friend-request"),
    path("friends/requests/<int:request_id>/reject/", RejectFriendRequestView.as_view(), name="reject-friend-request"),
    path("friends/<int:friend_id>/remove/", RemoveFriendView.as_view(), name="remove-friend"),
]
