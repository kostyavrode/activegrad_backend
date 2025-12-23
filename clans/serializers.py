from rest_framework import serializers
from .models import Clan


class ClanSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о клане."""
    member_count = serializers.IntegerField(source='get_member_count', read_only=True)
    captured_landmarks_count = serializers.IntegerField(source='get_captured_landmarks_count', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Clan
        fields = [
            'id', 'name', 'description', 'created_at', 
            'created_by_id', 'created_by_username',
            'member_count', 'captured_landmarks_count'
        ]
        read_only_fields = ['id', 'created_at', 'created_by_id', 'created_by_username', 'member_count', 'captured_landmarks_count']


class CreateClanSerializer(serializers.Serializer):
    """Сериализатор для создания клана."""
    name = serializers.CharField(max_length=20, required=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_name(self, value):
        """Валидация названия клана."""
        try:
            validated_name = Clan.validate_clan_name(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        
        # Проверка уникальности названия (без учета регистра)
        if Clan.objects.filter(name__iexact=validated_name).exists():
            raise serializers.ValidationError("Клан с таким названием уже существует")
        
        return validated_name
    
    def validate(self, data):
        """Дополнительная валидация данных."""
        return data


class JoinClanSerializer(serializers.Serializer):
    """Сериализатор для вступления в клан."""
    clan_id = serializers.IntegerField(required=True)
    
    def validate_clan_id(self, value):
        """Проверяет, что клан существует."""
        try:
            clan = Clan.objects.get(id=value)
        except Clan.DoesNotExist:
            raise serializers.ValidationError("Клан не найден")
        return value

