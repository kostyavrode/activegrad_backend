from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserClothesSerializer, CustomTokenObtainPairSerializer

User = get_user_model()

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