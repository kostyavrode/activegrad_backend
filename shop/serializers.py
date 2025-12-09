from rest_framework import serializers
from .models import ShopItem, UserPromoCode, PurchaseHistory
from django.contrib.auth import get_user_model

User = get_user_model()


class ShopItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товара в магазине"""
    
    class Meta:
        model = ShopItem
        fields = ['id', 'name', 'description', 'image_url', 'price', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PurchaseItemSerializer(serializers.Serializer):
    """Сериализатор для покупки товара"""
    item_id = serializers.IntegerField(required=True, help_text="ID товара для покупки")


class PurchaseResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа после покупки"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    item_name = serializers.CharField()
    price_paid = serializers.IntegerField()
    remaining_coins = serializers.IntegerField()
    promo_code = serializers.CharField()


class UserPromoCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для промокода пользователя"""
    shop_item_name = serializers.CharField(source='shop_item.name', read_only=True)
    shop_item_id = serializers.IntegerField(source='shop_item.id', read_only=True)
    
    class Meta:
        model = UserPromoCode
        fields = ['id', 'shop_item_id', 'shop_item_name', 'promo_code', 'purchased_at']
        read_only_fields = ['id', 'purchased_at']


class DeletePromoCodeSerializer(serializers.Serializer):
    """Сериализатор для удаления промокода"""
    promo_code_id = serializers.IntegerField(required=True, help_text="ID промокода для удаления")

