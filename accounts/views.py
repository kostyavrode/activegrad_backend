from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()
CustomUser = User  # Для совместимости
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserClothesSerializer, 
    CustomTokenObtainPairSerializer, FriendRequestSerializer, SendFriendRequestSerializer,
    FriendshipSerializer, UserBasicSerializer, ClanSerializer, CreateClanSerializer, JoinClanSerializer
)
from .models import FriendRequest, Friendship, Clan

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Генерация JWT токенов
            refresh = RefreshToken.for_user(user)

            return Response({
                "success": True,
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response({
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "player_id": user.id,  # Явно добавляем player_id для удобства
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "coins": user.coins,
                    "experience": user.experience,
                    "level": user.level,
                    "experience_to_next_level": user.get_experience_to_next_level(),
                }
            }, status=status.HTTP_200_OK)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class UpdateClothesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        serializer = UserClothesSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Clothes updated successfully",
                "clothes": serializer.data,
            })
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)


class GetPlayerInfoView(APIView):
    """
    API endpoint для получения информации о другом игроке по его ID.
    Возвращает никнейм, имя, фамилию, дату регистрации, пол и список достопримечательностей.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id):
        try:
            player_id = int(player_id)
        except (ValueError, TypeError):
            return Response({
                "success": False,
                "error": "player_id must be a valid integer"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем игрока
        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Player with ID {player_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Получаем достопримечательности игрока
        try:
            from landmarks.models import PlayerLandmarkObservation
            observations = PlayerLandmarkObservation.objects.filter(player=player)
            external_ids = [obs.external_id for obs in observations]
        except Exception:
            # Если landmarks app не доступен, возвращаем пустой список
            external_ids = []

        # Форматируем дату регистрации
        registration_date = player.registration_date.isoformat() if player.registration_date else None

        return Response({
            "success": True,
            "player": {
                "id": player.id,
                "player_id": player.id,
                "username": player.username,
                "first_name": player.first_name or "",
                "last_name": player.last_name or "",
                "registration_date": registration_date,
                "gender": player.gender if hasattr(player, 'gender') else None,
                "landmarks": {
                    "external_ids": external_ids,
                    "total_count": len(external_ids)
                }
            }
        }, status=status.HTTP_200_OK)


class GetPlayerLandmarksView(APIView):
    """
    API endpoint для получения списка всех достопримечательностей по ID пользователя.
    Возвращает только список external_ids (ID из Wikipedia API).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id):
        try:
            player_id = int(player_id)
        except (ValueError, TypeError):
            return Response({
                "success": False,
                "error": "player_id must be a valid integer"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем игрока
        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Player with ID {player_id} not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Получаем достопримечательности игрока
        try:
            from landmarks.models import PlayerLandmarkObservation
            observations = PlayerLandmarkObservation.objects.filter(player=player).order_by('-observed_at')
            external_ids = [obs.external_id for obs in observations]
        except Exception as e:
            # Если landmarks app не доступен, возвращаем ошибку
            return Response({
                "success": False,
                "error": "Landmarks service is not available"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "success": True,
            "player_id": player.id,
            "player_username": player.username,
            "external_ids": external_ids,
            "total_count": len(external_ids)
        }, status=status.HTTP_200_OK)


class GetCurrentUserStatsView(APIView):
    """
    API endpoint для получения статистики текущего авторизованного пользователя.
    Возвращает монеты, опыт, уровень и другую информацию.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        return Response({
            "success": True,
            "player_stats": {
                "id": user.id,
                "player_id": user.id,
                "username": user.username,
                "coins": user.coins,
                "experience": user.experience,
                "level": user.level,
                "experience_to_next_level": user.get_experience_to_next_level(),
                "experience_per_level": user.EXPERIENCE_PER_LEVEL,
                "progress_to_next_level_percent": round(
                    (user.experience / user.EXPERIENCE_PER_LEVEL) * 100, 
                    2
                ) if user.EXPERIENCE_PER_LEVEL > 0 else 0
            }
        }, status=status.HTTP_200_OK)


class GetCurrentUserCoinsView(APIView):
    """
    API endpoint для получения только количества монет текущего авторизованного пользователя.
    Легковесный endpoint для быстрой проверки баланса.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        return Response({
            "success": True,
            "coins": user.coins,
            "player_id": user.id
        }, status=status.HTTP_200_OK)


# ========== FRIEND SYSTEM VIEWS ==========

class SendFriendRequestView(APIView):
    """
    API endpoint для отправки запроса дружбы другому пользователю.
    POST /api/friends/requests/send/
    Body: {"to_user_id": 123}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendFriendRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from_user = request.user
        to_user_id = serializer.validated_data['to_user_id']
        
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, что пользователь не отправляет запрос самому себе
        if from_user == to_user:
            return Response({
                "success": False,
                "error": "Cannot send friend request to yourself"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, не являются ли они уже друзьями
        if Friendship.are_friends(from_user, to_user):
            return Response({
                "success": False,
                "error": "You are already friends with this user"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, есть ли уже активный запрос
        existing_request = FriendRequest.objects.filter(
            (Q(from_user=from_user) & Q(to_user=to_user)) |
            (Q(from_user=to_user) & Q(to_user=from_user)),
            status='pending'
        ).first()
        
        if existing_request:
            if existing_request.from_user == from_user:
                return Response({
                    "success": False,
                    "error": "Friend request already sent"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "success": False,
                    "error": "This user has already sent you a friend request. Please accept it instead."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаём новый запрос
        friend_request = FriendRequest.objects.create(
            from_user=from_user,
            to_user=to_user,
            status='pending'
        )
        
        return Response({
            "success": True,
            "message": "Friend request sent successfully",
            "friend_request": FriendRequestSerializer(friend_request).data
        }, status=status.HTTP_201_CREATED)


class AcceptFriendRequestView(APIView):
    """
    API endpoint для принятия запроса дружбы.
    POST /api/friends/requests/<request_id>/accept/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            friend_request = FriendRequest.objects.get(id=request_id, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({
                "success": False,
                "error": "Friend request not found or already processed"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, что текущий пользователь - получатель запроса
        if friend_request.to_user != request.user:
            return Response({
                "success": False,
                "error": "You are not authorized to accept this request"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Проверяем, не являются ли они уже друзьями
        if Friendship.are_friends(friend_request.from_user, friend_request.to_user):
            friend_request.status = 'accepted'
            friend_request.save()
            return Response({
                "success": False,
                "error": "You are already friends"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаём дружбу (порядок user1 < user2 для избежания дубликатов)
        user1, user2 = sorted([friend_request.from_user, friend_request.to_user], key=lambda u: u.id)
        friendship = Friendship.objects.create(user1=user1, user2=user2)
        
        # Обновляем статус запроса
        friend_request.status = 'accepted'
        friend_request.save()
        
        return Response({
            "success": True,
            "message": "Friend request accepted",
            "friendship": FriendshipSerializer(friendship, context={'request': request}).data
        }, status=status.HTTP_200_OK)


class RejectFriendRequestView(APIView):
    """
    API endpoint для отклонения запроса дружбы.
    POST /api/friends/requests/<request_id>/reject/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        try:
            friend_request = FriendRequest.objects.get(id=request_id, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({
                "success": False,
                "error": "Friend request not found or already processed"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, что текущий пользователь - получатель запроса
        if friend_request.to_user != request.user:
            return Response({
                "success": False,
                "error": "You are not authorized to reject this request"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Обновляем статус запроса
        friend_request.status = 'rejected'
        friend_request.save()
        
        return Response({
            "success": True,
            "message": "Friend request rejected"
        }, status=status.HTTP_200_OK)


class GetFriendsListView(APIView):
    """
    API endpoint для получения списка всех друзей текущего пользователя.
    GET /api/friends/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        friends = Friendship.get_friends(user)
        
        # Формируем список дружеских отношений с информацией о друге
        friendships = Friendship.objects.filter(
            Q(user1=user) | Q(user2=user)
        )
        
        serializer = FriendshipSerializer(friendships, many=True, context={'request': request})
        
        # Извлекаем только информацию о друзьях из сериализатора
        friends_data = []
        for item in serializer.data:
            if item.get('friend'):
                friends_data.append(item['friend'])
        
        return Response({
            "success": True,
            "friends": friends_data,
            "total_count": len(friends_data)
        }, status=status.HTTP_200_OK)


class GetPendingFriendRequestsView(APIView):
    """
    API endpoint для получения входящих запросов дружбы (которые отправили текущему пользователю).
    GET /api/friends/requests/pending/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        pending_requests = FriendRequest.objects.filter(
            to_user=user,
            status='pending'
        ).order_by('-created_at')
        
        serializer = FriendRequestSerializer(pending_requests, many=True)
        
        return Response({
            "success": True,
            "pending_requests": serializer.data,
            "total_count": len(serializer.data)
        }, status=status.HTTP_200_OK)


class GetSentFriendRequestsView(APIView):
    """
    API endpoint для получения отправленных запросов дружбы (которые отправил текущий пользователь).
    GET /api/friends/requests/sent/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        sent_requests = FriendRequest.objects.filter(
            from_user=user,
            status='pending'
        ).order_by('-created_at')
        
        serializer = FriendRequestSerializer(sent_requests, many=True)
        
        return Response({
            "success": True,
            "sent_requests": serializer.data,
            "total_count": len(serializer.data)
        }, status=status.HTTP_200_OK)


class RemoveFriendView(APIView):
    """
    API endpoint для удаления друга.
    DELETE /api/friends/<friend_id>/remove/
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend_id):
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        user = request.user
        
        # Проверяем, являются ли они друзьями
        if not Friendship.are_friends(user, friend):
            return Response({
                "success": False,
                "error": "You are not friends with this user"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Удаляем дружбу
        friendship = Friendship.objects.filter(
            (Q(user1=user) & Q(user2=friend)) |
            (Q(user1=friend) & Q(user2=user))
        ).first()
        
        if friendship:
            friendship.delete()
            
            # Также обновляем статус всех связанных запросов дружбы
            FriendRequest.objects.filter(
                ((Q(from_user=user) & Q(to_user=friend)) |
                 (Q(from_user=friend) & Q(to_user=user))),
                status='accepted'
            ).update(status='cancelled')
        
        return Response({
            "success": True,
            "message": "Friend removed successfully"
        }, status=status.HTTP_200_OK)


# ========== CLAN SYSTEM VIEWS ==========

class CreateClanView(APIView):
    """
    API endpoint для создания нового клана.
    POST /api/accounts/clans/create/
    Body: {"name": "MyClan", "description": "Описание (опционально)"}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateClanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Проверяем, не состоит ли пользователь уже в каком-то клане
        if user.clan is not None:
            return Response({
                "success": False,
                "error": "You are already in a clan. Leave your current clan first."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем клан
        clan = Clan.objects.create(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            created_by=user
        )
        
        # Присоединяем создателя к клану
        user.clan = clan
        user.save()
        
        return Response({
            "success": True,
            "message": "Clan created successfully",
            "clan": ClanSerializer(clan).data
        }, status=status.HTTP_201_CREATED)


class JoinClanView(APIView):
    """
    API endpoint для вступления в клан.
    POST /api/accounts/clans/join/
    Body: {"clan_id": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = JoinClanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        clan_id = serializer.validated_data['clan_id']
        
        try:
            clan = Clan.objects.get(id=clan_id)
        except Clan.DoesNotExist:
            return Response({
                "success": False,
                "error": "Clan not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, не состоит ли пользователь уже в каком-то клане
        if user.clan is not None:
            if user.clan.id == clan_id:
                return Response({
                    "success": False,
                    "error": "You are already in this clan"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "success": False,
                    "error": "You are already in another clan. Leave your current clan first."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Присоединяем пользователя к клану
        user.clan = clan
        user.save()
        
        return Response({
            "success": True,
            "message": f"You have joined the clan '{clan.name}'",
            "clan": ClanSerializer(clan).data
        }, status=status.HTTP_200_OK)


class LeaveClanView(APIView):
    """
    API endpoint для покидания клана.
    POST /api/accounts/clans/leave/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Проверяем, состоит ли пользователь в клане
        if user.clan is None:
            return Response({
                "success": False,
                "error": "You are not in any clan"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        clan_name = user.clan.name
        clan_id = user.clan.id
        
        # Покидаем клан
        user.clan = None
        user.save()
        
        # Проверяем, не остался ли клан пустым (если создатель покинул)
        clan = Clan.objects.get(id=clan_id)
        if clan.members.count() == 0:
            # Если клан пуст, удаляем его (или можно оставить, решать вам)
            # Пока оставим клан, но он будет пустым
            pass
        
        return Response({
            "success": True,
            "message": f"You have left the clan '{clan_name}'"
        }, status=status.HTTP_200_OK)


class SearchClansView(APIView):
    """
    API endpoint для поиска кланов.
    GET /api/accounts/clans/search/?query=name
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        
        if not query:
            return Response({
                "success": False,
                "error": "Query parameter is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Поиск кланов по названию (без учета регистра)
        clans = Clan.objects.filter(name__icontains=query).order_by('name')[:20]  # Ограничиваем 20 результатами
        
        serializer = ClanSerializer(clans, many=True)
        
        return Response({
            "success": True,
            "clans": serializer.data,
            "total_count": len(serializer.data),
            "query": query
        }, status=status.HTTP_200_OK)


class TopClansView(APIView):
    """
    API endpoint для получения топ-10 лучших кланов.
    GET /api/accounts/clans/top/
    
    Рейтинг определяется по количеству участников клана.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Получаем топ-10 кланов по количеству участников
        # Используем annotate для подсчета участников и сортировки
        from django.db.models import Count
        top_clans = Clan.objects.annotate(
            member_count=Count('members')
        ).filter(member_count__gt=0).order_by('-member_count', '-created_at')[:10]
        
        serializer = ClanSerializer(top_clans, many=True)
        
        return Response({
            "success": True,
            "top_clans": serializer.data,
            "total_count": len(serializer.data)
        }, status=status.HTTP_200_OK)