from rest_framework import serializers
from .models import Landmark, PlayerLandmarkObservation
from django.contrib.auth import get_user_model

User = get_user_model()


class LandmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landmark
        fields = ["id", "name", "description", "external_id"]


class PlayerLandmarkObservationSerializer(serializers.ModelSerializer):
    landmark = LandmarkSerializer(read_only=True)
    landmark_id = serializers.IntegerField(write_only=True, required=False)
    player_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = PlayerLandmarkObservation
        fields = ["id", "player_id", "landmark", "landmark_id", "observed_at"]
        read_only_fields = ["id", "observed_at"]


class SavePlayerLandmarksSerializer(serializers.Serializer):
    player_id = serializers.IntegerField(required=True)
    landmark_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False
    )


class PlayerLandmarksResponseSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    player_username = serializers.CharField()
    landmarks = LandmarkSerializer(many=True)

