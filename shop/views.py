from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from .models import ShopItem, UserPromoCode, PurchaseHistory
from .serializers import (
    ShopItemSerializer,
    PurchaseItemSerializer,
    PurchaseResponseSerializer,
    UserPromoCodeSerializer,
    DeletePromoCodeSerializer
)


class ShopItemsListView(APIView):
    """
    API endpoint для получения списка всех активных товаров в магазине.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = ShopItem.objects.filter(is_active=True)
        serializer = ShopItemSerializer(items, many=True)
        return Response({
            "success": True,
            "items": serializer.data,
            "total_count": len(serializer.data)
        }, status=status.HTTP_200_OK)


class PurchaseItemView(APIView):
    """
    API endpoint для покупки товара.
    Проверяет баланс пользователя, списывает деньги и выдает промокод.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PurchaseItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        item_id = serializer.validated_data['item_id']
        user = request.user

        # Получаем товар
        try:
            item = ShopItem.objects.get(id=item_id, is_active=True)
        except ShopItem.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Item with ID {item_id} not found or not available"
            }, status=status.HTTP_404_NOT_FOUND)

        # Проверяем баланс
        if user.coins < item.price:
            return Response({
                "success": False,
                "error": "Insufficient funds",
                "message": f"You have {user.coins} coins, but need {item.price} coins",
                "required": item.price,
                "available": user.coins
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, не купил ли пользователь уже этот товар (опционально - можно убрать, если разрешить повторные покупки)
        # Если нужно разрешить только одну покупку каждого товара, раскомментируйте:
        # if UserPromoCode.objects.filter(user=user, shop_item=item).exists():
        #     return Response({
        #         "success": False,
        #         "error": "You have already purchased this item"
        #     }, status=status.HTTP_400_BAD_REQUEST)

        # Списываем деньги
        user.coins -= item.price
        user.save()

        # Создаем запись о промокоде
        user_promo_code, created = UserPromoCode.objects.get_or_create(
            user=user,
            shop_item=item,
            promo_code=item.promo_code,
            defaults={'promo_code': item.promo_code}
        )

        # Сохраняем в историю покупок
        PurchaseHistory.objects.create(
            user=user,
            shop_item=item,
            price_paid=item.price,
            promo_code=item.promo_code
        )

        return Response({
            "success": True,
            "message": f"Successfully purchased {item.name}",
            "item_name": item.name,
            "price_paid": item.price,
            "remaining_coins": user.coins,
            "promo_code": item.promo_code
        }, status=status.HTTP_200_OK)


class UserPromoCodesView(APIView):
    """
    API endpoint для получения списка промокодов пользователя.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        promo_codes = UserPromoCode.objects.filter(user=user)
        serializer = UserPromoCodeSerializer(promo_codes, many=True)
        return Response({
            "success": True,
            "promo_codes": serializer.data,
            "total_count": len(serializer.data)
        }, status=status.HTTP_200_OK)


class DeletePromoCodeView(APIView):
    """
    API endpoint для удаления промокода пользователя.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, promo_code_id=None):
        # Получаем promo_code_id из URL или из тела запроса
        if not promo_code_id:
            serializer = DeletePromoCodeSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            promo_code_id = serializer.validated_data['promo_code_id']
        else:
            try:
                promo_code_id = int(promo_code_id)
            except (ValueError, TypeError):
                return Response({
                    "success": False,
                    "error": "promo_code_id must be a valid integer"
                }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Получаем промокод
        try:
            promo_code = UserPromoCode.objects.get(id=promo_code_id, user=user)
        except UserPromoCode.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Promo code with ID {promo_code_id} not found or does not belong to you"
            }, status=status.HTTP_404_NOT_FOUND)

        # Удаляем промокод
        promo_code.delete()

        return Response({
            "success": True,
            "message": f"Promo code {promo_code.promo_code} deleted successfully"
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """Альтернативный способ удаления через POST (для удобства)"""
        return self.delete(request)

