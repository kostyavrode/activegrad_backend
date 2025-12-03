from rest_framework import serializers
from .models import PlayerLandmarkObservation
from django.contrib.auth import get_user_model

User = get_user_model()


class PlayerLandmarkObservationSerializer(serializers.ModelSerializer):
    """Сериализатор для модели наблюдения игрока в достопримечательности"""
    player_id = serializers.IntegerField(read_only=True, source='player.id')
    player_username = serializers.CharField(read_only=True, source='player.username')
    
    class Meta:
        model = PlayerLandmarkObservation
        fields = ["id", "player_id", "player_username", "external_id", "observed_at"]
        read_only_fields = ["id", "observed_at"]


class SavePlayerLandmarksSerializer(serializers.Serializer):
    """
    Сериализатор для сохранения достопримечательностей, где был игрок.
    Принимает player_id и список external_ids (ID из Wikipedia API).
    """
    player_id = serializers.IntegerField(required=True)
    external_ids = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False,
        help_text="Список ID достопримечательностей из Wikipedia API"
    )


class PlayerLandmarksResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа с достопримечательностями игрока"""
    player_id = serializers.IntegerField()
    player_username = serializers.CharField()
    external_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="Список ID достопримечательностей, где был игрок"
    )
    total_count = serializers.IntegerField()

