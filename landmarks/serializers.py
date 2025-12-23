from rest_framework import serializers
from .models import PlayerLandmarkObservation, LandmarkCapture
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


class CaptureLandmarkSerializer(serializers.Serializer):
    """Сериализатор для запроса захвата достопримечательности"""
    external_id = serializers.CharField(
        required=True,
        help_text="ID достопримечательности из Wikipedia API"
    )
    
    def validate_external_id(self, value):
        """Валидация external_id"""
        if not value or not value.strip():
            raise serializers.ValidationError("external_id cannot be empty")
        return value.strip()


class LandmarkCaptureSerializer(serializers.ModelSerializer):
    """Сериализатор для модели захвата достопримечательности"""
    captured_by_username = serializers.CharField(read_only=True, source='captured_by.username')
    captured_by_id = serializers.IntegerField(read_only=True, source='captured_by.id')
    clan_name = serializers.CharField(read_only=True, source='clan.name', allow_null=True)
    clan_id = serializers.IntegerField(read_only=True, source='clan.id', allow_null=True)
    
    class Meta:
        model = LandmarkCapture
        fields = [
            'id', 'external_id', 'captured_by_id', 'captured_by_username',
            'clan_id', 'clan_name', 'captured_at'
        ]
        read_only_fields = ['id', 'captured_by_id', 'captured_by_username', 'clan_id', 'clan_name', 'captured_at']

