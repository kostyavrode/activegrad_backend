import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction

from .models import PlayerInventory, CraftRecipe, UpgradeConfig
from .serializers import UpgradeRequestSerializer


def get_or_create_inventory(user):
    """Получает или создаёт инвентарь для пользователя."""
    inventory, created = PlayerInventory.objects.get_or_create(
        user=user,
        defaults={'metal': 0, 'wood': 0, 'blueprints': 0}
    )
    return inventory


class InventoryView(APIView):
    """
    GET /api/inventory/
    Возвращает инвентарь текущего игрока: ресурсы и предметы.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory = get_or_create_inventory(request.user)
        data = {
            'resources': {
                'metal': inventory.metal,
                'wood': inventory.wood,
                'blueprints': inventory.blueprints,
            },
            'items': {
                'sword': {
                    'has_item': inventory.has_sword(),
                    'sharpness': inventory.sword_sharpness if inventory.has_sword() else None,
                },
                'shield': {
                    'has_item': inventory.has_shield(),
                    'durability': inventory.shield_durability if inventory.has_shield() else None,
                },
            },
        }
        return Response({'success': True, 'inventory': data}, status=status.HTTP_200_OK)


class RecipesView(APIView):
    """
    GET /api/inventory/recipes/
    Возвращает актуальные рецепты крафта.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recipes = CraftRecipe.objects.filter(is_active=True)
        data = {}
        for r in recipes:
            data[r.item_type] = {
                'metal_required': r.metal_required,
                'wood_required': r.wood_required,
                'blueprints_required': r.blueprints_required,
            }
        return Response({'success': True, 'recipes': data}, status=status.HTTP_200_OK)


class CraftSwordView(APIView):
    """
    POST /api/inventory/craft/sword/
    Крафт меча по рецепту.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        recipe = CraftRecipe.objects.filter(item_type='sword', is_active=True).first()
        if not recipe:
            return Response({
                'success': False,
                'error': 'Recipe for sword not found'
            }, status=status.HTTP_404_NOT_FOUND)

        inventory = get_or_create_inventory(request.user)

        if inventory.has_sword():
            return Response({
                'success': False,
                'error': 'You already have a sword'
            }, status=status.HTTP_400_BAD_REQUEST)

        if (inventory.metal < recipe.metal_required or
                inventory.wood < recipe.wood_required or
                inventory.blueprints < recipe.blueprints_required):
            return Response({
                'success': False,
                'error': 'Insufficient resources',
                'required': recipe.get_requirements(),
                'current': {
                    'metal': inventory.metal,
                    'wood': inventory.wood,
                    'blueprints': inventory.blueprints,
                },
            }, status=status.HTTP_400_BAD_REQUEST)

        inventory.metal -= recipe.metal_required
        inventory.wood -= recipe.wood_required
        inventory.blueprints -= recipe.blueprints_required
        inventory.sword_sharpness = 1
        inventory.save()

        return Response({
            'success': True,
            'message': 'Sword crafted successfully',
            'inventory': {
                'resources': {'metal': inventory.metal, 'wood': inventory.wood, 'blueprints': inventory.blueprints},
                'sword': {'sharpness': 1},
            },
        }, status=status.HTTP_200_OK)


class CraftShieldView(APIView):
    """
    POST /api/inventory/craft/shield/
    Крафт щита по рецепту.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        recipe = CraftRecipe.objects.filter(item_type='shield', is_active=True).first()
        if not recipe:
            return Response({
                'success': False,
                'error': 'Recipe for shield not found'
            }, status=status.HTTP_404_NOT_FOUND)

        inventory = get_or_create_inventory(request.user)

        if inventory.has_shield():
            return Response({
                'success': False,
                'error': 'You already have a shield'
            }, status=status.HTTP_400_BAD_REQUEST)

        if (inventory.metal < recipe.metal_required or
                inventory.wood < recipe.wood_required or
                inventory.blueprints < recipe.blueprints_required):
            return Response({
                'success': False,
                'error': 'Insufficient resources',
                'required': recipe.get_requirements(),
                'current': {
                    'metal': inventory.metal,
                    'wood': inventory.wood,
                    'blueprints': inventory.blueprints,
                },
            }, status=status.HTTP_400_BAD_REQUEST)

        inventory.metal -= recipe.metal_required
        inventory.wood -= recipe.wood_required
        inventory.blueprints -= recipe.blueprints_required
        inventory.shield_durability = 1
        inventory.save()

        return Response({
            'success': True,
            'message': 'Shield crafted successfully',
            'inventory': {
                'resources': {'metal': inventory.metal, 'wood': inventory.wood, 'blueprints': inventory.blueprints},
                'shield': {'durability': 1},
            },
        }, status=status.HTTP_200_OK)


class UpgradeSwordView(APIView):
    """
    POST /api/inventory/upgrade/sword/
    Улучшение меча. В теле: metal, wood, blueprints — сколько ресурсов использовать.
    Ответ: upgraded (bool), probability (float), new_sharpness (int | null).
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = UpgradeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        metal = serializer.validated_data['metal']
        wood = serializer.validated_data['wood']
        blueprints = serializer.validated_data['blueprints']

        if metal == 0 and wood == 0 and blueprints == 0:
            return Response({
                'success': False,
                'error': 'Provide at least one resource for upgrade'
            }, status=status.HTTP_400_BAD_REQUEST)

        config = UpgradeConfig.objects.filter(item_type='sword', is_active=True).first()
        if not config:
            return Response({
                'success': False,
                'error': 'Upgrade config for sword not found'
            }, status=status.HTTP_404_NOT_FOUND)

        inventory = get_or_create_inventory(request.user)

        if not inventory.has_sword():
            return Response({
                'success': False,
                'error': 'You do not have a sword to upgrade'
            }, status=status.HTTP_400_BAD_REQUEST)

        if (inventory.metal < metal or inventory.wood < wood or inventory.blueprints < blueprints):
            return Response({
                'success': False,
                'error': 'Insufficient resources',
                'requested': {'metal': metal, 'wood': wood, 'blueprints': blueprints},
                'current': {
                    'metal': inventory.metal,
                    'wood': inventory.wood,
                    'blueprints': inventory.blueprints,
                },
            }, status=status.HTTP_400_BAD_REQUEST)

        probability = config.calculate_probability(metal, wood, blueprints)
        roll = random.uniform(0, 100)
        upgraded = roll < probability

        if upgraded:
            inventory.metal -= metal
            inventory.wood -= wood
            inventory.blueprints -= blueprints
            inventory.sword_sharpness += 1
            inventory.save()

        return Response({
            'success': True,
            'upgraded': upgraded,
            'probability': round(probability, 2),
            'roll': round(roll, 2),
            'sword_sharpness': inventory.sword_sharpness,
        }, status=status.HTTP_200_OK)


class UpgradeShieldView(APIView):
    """
    POST /api/inventory/upgrade/shield/
    Улучшение щита. В теле: metal, wood, blueprints.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = UpgradeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        metal = serializer.validated_data['metal']
        wood = serializer.validated_data['wood']
        blueprints = serializer.validated_data['blueprints']

        if metal == 0 and wood == 0 and blueprints == 0:
            return Response({
                'success': False,
                'error': 'Provide at least one resource for upgrade'
            }, status=status.HTTP_400_BAD_REQUEST)

        config = UpgradeConfig.objects.filter(item_type='shield', is_active=True).first()
        if not config:
            return Response({
                'success': False,
                'error': 'Upgrade config for shield not found'
            }, status=status.HTTP_404_NOT_FOUND)

        inventory = get_or_create_inventory(request.user)

        if not inventory.has_shield():
            return Response({
                'success': False,
                'error': 'You do not have a shield to upgrade'
            }, status=status.HTTP_400_BAD_REQUEST)

        if (inventory.metal < metal or inventory.wood < wood or inventory.blueprints < blueprints):
            return Response({
                'success': False,
                'error': 'Insufficient resources',
                'requested': {'metal': metal, 'wood': wood, 'blueprints': blueprints},
                'current': {
                    'metal': inventory.metal,
                    'wood': inventory.wood,
                    'blueprints': inventory.blueprints,
                },
            }, status=status.HTTP_400_BAD_REQUEST)

        probability = config.calculate_probability(metal, wood, blueprints)
        roll = random.uniform(0, 100)
        upgraded = roll < probability

        if upgraded:
            inventory.metal -= metal
            inventory.wood -= wood
            inventory.blueprints -= blueprints
            inventory.shield_durability += 1
            inventory.save()

        return Response({
            'success': True,
            'upgraded': upgraded,
            'probability': round(probability, 2),
            'roll': round(roll, 2),
            'shield_durability': inventory.shield_durability,
        }, status=status.HTTP_200_OK)
