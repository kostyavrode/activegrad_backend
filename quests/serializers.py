from rest_framework import serializers
from .models import Quest, QuestProgress, DailyQuest, QuestPromoCode


class QuestSerializer(serializers.ModelSerializer):
    """Сериализатор для квеста с всеми обязательными полями"""
    
    class Meta:
        model = Quest
        fields = [
            "id",
            "type",
            "title",
            "description",
            "count",
            "reward_type",
            "reward_amount",
            "promo_code",
            "image_url"
        ]
        read_only_fields = ["id"]
    
    def validate_type(self, value):
        """Валидация типа квеста - не может быть пустым"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Поле type не может быть пустым!")
        # Маппинг visit_sights на mark_sights
        if value == 'visit_sights':
            return 'mark_sights'
        return value
    
    def validate_count(self, value):
        """Валидация count - должно быть > 0"""
        if value <= 0:
            raise serializers.ValidationError("Поле count должно быть больше 0")
        return value
    
    def validate_reward_amount(self, value):
        """Валидация reward_amount - должно быть >= 0"""
        if value < 0:
            raise serializers.ValidationError("Поле reward_amount должно быть >= 0")
        return value
    
    def to_representation(self, instance):
        """Убеждаемся, что type всегда присутствует и не пустой"""
        data = super().to_representation(instance)
        # Если type пустой или None, не возвращаем квест (фильтруем на уровне view)
        if not data.get('type') or data.get('type').strip() == '':
            return None
        return data


class QuestCompleteSerializer(serializers.Serializer):
    """Сериализатор для завершения квеста"""
    player_id = serializers.IntegerField(required=True, help_text="ID игрока")


class QuestProgressSerializer(serializers.ModelSerializer):
    """Сериализатор для прогресса квеста"""
    quest_id = serializers.IntegerField(source='quest.id', read_only=True)
    required_count = serializers.IntegerField(source='quest.count', read_only=True)
    
    class Meta:
        model = QuestProgress
        fields = [
            "quest_id",
            "current_progress",
            "required_count",
            "is_completed",
            "reward_claimed"
        ]


class QuestPromoCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для промокода, полученного за квест"""
    quest_id = serializers.IntegerField(source='quest.id', read_only=True)
    quest_title = serializers.CharField(source='quest.title', read_only=True)
    quest_description = serializers.CharField(source='quest.description', read_only=True)
    quest_image_url = serializers.URLField(source='quest.image_url', read_only=True)
    
    class Meta:
        model = QuestPromoCode
        fields = [
            'id',
            'quest_id',
            'quest_title',
            'quest_description',
            'quest_image_url',
            'promo_code',
            'date',
            'obtained_at'
        ]
        read_only_fields = ['id', 'obtained_at']
