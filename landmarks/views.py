from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import PlayerLandmarkObservation
from .serializers import SavePlayerLandmarksSerializer

User = get_user_model()


class SavePlayerLandmarksView(APIView):
    """
    API endpoint для сохранения факта того, что игрок был в достопримечательности.
    Принимает player_id и список external_ids (ID из Wikipedia API).
    Названия и описания достопримечательностей получаются из Unity через Wikipedia API.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SavePlayerLandmarksSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=400)

        player_id = serializer.validated_data['player_id']
        external_ids = serializer.validated_data['external_ids']

        # Получаем игрока
        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Player with ID {player_id} not found"
            }, status=404)

        # Сохраняем наблюдения (unique_together предотвращает дубликаты)
        saved_external_ids = []
        
        for external_id in external_ids:
            # Убираем пробелы и проверяем, что external_id не пустой
            external_id = external_id.strip()
            if not external_id:
                continue
                
            # Создаем или получаем наблюдение (unique_together предотвращает дубликаты)
            observation, created = PlayerLandmarkObservation.objects.get_or_create(
                player=player,
                external_id=external_id
            )
            if created:
                saved_external_ids.append(external_id)

        return Response({
            "success": True,
            "message": f"Successfully saved {len(saved_external_ids)} landmark observation(s)",
            "player_id": player_id,
            "saved_external_ids": saved_external_ids,
            "total_saved": len(saved_external_ids)
        }, status=200)


class GetPlayerLandmarksView(APIView):
    """
    API endpoint для получения списка ID достопримечательностей, где был игрок.
    Принимает player_id как query параметр или в URL path.
    Возвращает список external_ids (ID из Wikipedia API).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None):
        # Получаем player_id из URL path или query параметра
        player_id = player_id or request.query_params.get('player_id')
        
        if not player_id:
            return Response({
                "success": False,
                "error": "player_id is required"
            }, status=400)

        try:
            player_id = int(player_id)
        except (ValueError, TypeError):
            return Response({
                "success": False,
                "error": "player_id must be a valid integer"
            }, status=400)

        # Получаем игрока
        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Player with ID {player_id} not found"
            }, status=404)

        # Получаем все наблюдения игрока
        observations = PlayerLandmarkObservation.objects.filter(player=player)
        external_ids = [obs.external_id for obs in observations]
        
        return Response({
            "success": True,
            "player_id": player.id,
            "player_username": player.username,
            "external_ids": external_ids,
            "total_count": len(external_ids)
        }, status=200)


class TestLandmarksView(APIView):
    """Тестовый endpoint для проверки доступности landmarks API"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "status": "OK",
            "message": "Landmarks API is working",
            "user": request.user.username,
            "user_id": request.user.id
        }, status=200)
    
    def post(self, request):
        return Response({
            "status": "OK",
            "message": "Landmarks API POST is working",
            "user": request.user.username,
            "user_id": request.user.id,
            "received_data": request.data
        }, status=200)
