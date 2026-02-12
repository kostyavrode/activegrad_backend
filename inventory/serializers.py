from rest_framework import serializers


class UpgradeRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса улучшения меча/щита."""
    metal = serializers.IntegerField(min_value=0, default=0)
    wood = serializers.IntegerField(min_value=0, default=0)
    blueprints = serializers.IntegerField(min_value=0, default=0)
