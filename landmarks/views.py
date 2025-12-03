from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Landmark, PlayerLandmarkObservation
from .serializers import SavePlayerLandmarksSerializer, LandmarkSerializer

User = get_user_model()


class SavePlayerLandmarksView(APIView):
    """
    API endpoint to save landmarks where a player has been observed.
    Accepts player_id and a list of landmark_ids.
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
        landmark_ids = serializer.validated_data['landmark_ids']

        # Get the player
        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Player with ID {player_id} not found"
            }, status=404)

        # Get or create landmarks
        saved_landmarks = []
        errors = []
        
        for landmark_id in landmark_ids:
            try:
                landmark = Landmark.objects.get(id=landmark_id)
                # Create or get the observation (unique_together ensures no duplicates)
                observation, created = PlayerLandmarkObservation.objects.get_or_create(
                    player=player,
                    landmark=landmark
                )
                if created:
                    saved_landmarks.append(landmark_id)
            except Landmark.DoesNotExist:
                errors.append(f"Landmark with ID {landmark_id} not found")

        response_data = {
            "success": True,
            "message": f"Successfully saved {len(saved_landmarks)} landmark observation(s)",
            "player_id": player_id,
            "saved_landmark_ids": saved_landmarks
        }
        
        if errors:
            response_data["errors"] = errors
            response_data["message"] += f" with {len(errors)} error(s)"

        return Response(response_data, status=200 if not errors else 207)  # 207 Multi-Status if some failed


class GetPlayerLandmarksView(APIView):
    """
    API endpoint to retrieve all landmarks where a player has been observed.
    Accepts player_id as a query parameter or in the URL path.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None):
        # Get player_id from URL path or query parameter
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

        # Get the player
        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Player with ID {player_id} not found"
            }, status=404)

        # Get all landmarks where the player has been observed
        observations = PlayerLandmarkObservation.objects.filter(player=player).select_related('landmark')
        landmarks = [obs.landmark for obs in observations]

        landmark_serializer = LandmarkSerializer(landmarks, many=True)
        
        return Response({
            "success": True,
            "player_id": player.id,
            "player_username": player.username,
            "landmarks": landmark_serializer.data,
            "total_count": len(landmarks)
        }, status=200)
