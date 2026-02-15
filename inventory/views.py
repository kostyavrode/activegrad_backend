import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction

from .models import PlayerInventory, CraftRecipe, UpgradeConfig
from .serializers import UpgradeRequestSerializer


# Маппинг для универсального API (массивы + display_name)
RESOURCE_IDS = ['metal', 'wood', 'blueprints']
RESOURCE_DISPLAY_NAMES = {
    'metal': 'Металл',
    'wood': 'Дерево',
    'blueprints': 'Чертежи',
}
ITEM_DISPLAY_NAMES = {
    'sword': 'Меч',
    'shield': 'Щит',
}
ITEM_STAT_KEYS = {
    'sword': 'sharpness',
    'shield': 'durability',
}
RESOURCE_FIELDS = {
    'metal': 'metal',
    'wood': 'wood',
    'blueprints': 'blueprints',
}


def get_or_create_inventory(user):
    """Получает или создаёт инвентарь для пользователя."""
    inventory, created = PlayerInventory.objects.get_or_create(
        user=user,
        defaults={'metal': 0, 'wood': 0, 'blueprints': 0}
    )
    return inventory


def format_inventory_response(inventory):
    """Форматирует инвентарь в универсальный формат (массивы + display_name)."""
    resources = [
        {
            'id': rid,
            'amount': getattr(inventory, field),
            'display_name': RESOURCE_DISPLAY_NAMES[rid],
        }
        for rid, field in RESOURCE_FIELDS.items()
    ]
    items = []
    for item_id in ITEM_DISPLAY_NAMES:
        has_item = (item_id == 'sword' and inventory.has_sword()) or (item_id == 'shield' and inventory.has_shield())
        stat_key = ITEM_STAT_KEYS[item_id]
        stat_val = getattr(inventory, f'sword_sharpness' if item_id == 'sword' else 'shield_durability')
        item_data = {
            'id': item_id,
            'display_name': ITEM_DISPLAY_NAMES[item_id],
            'has_item': has_item,
        }
        item_data[stat_key] = stat_val if has_item else None
        items.append(item_data)
    return {'resources': resources, 'items': items}


class InventoryView(APIView):
    """
    GET /api/inventory/
    Возвращает инвентарь в универсальном формате: массивы ресурсов и предметов.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory = get_or_create_inventory(request.user)
        data = format_inventory_response(inventory)
        return Response({'success': True, **data}, status=status.HTTP_200_OK)


class RecipesView(APIView):
    """
    GET /api/inventory/recipes/
    Возвращает рецепты в универсальном формате: массив с requirements.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recipes = CraftRecipe.objects.filter(is_active=True)
        data = []
        for r in recipes:
            requirements = []
            for rid, field in RESOURCE_FIELDS.items():
                amount = getattr(r, f'{rid}_required')
                if amount > 0:
                    requirements.append({
                        'resource_id': rid,
                        'amount': amount,
                        'display_name': RESOURCE_DISPLAY_NAMES[rid],
                    })
            data.append({
                'id': r.item_type,
                'display_name': ITEM_DISPLAY_NAMES.get(r.item_type, r.get_item_type_display()),
                'requirements': requirements,
            })
        return Response({'success': True, 'recipes': data}, status=status.HTTP_200_OK)


class CraftItemView(APIView):
    """
    POST /api/inventory/craft/{item_id}/
    Универсальный крафт предмета по его ID (sword, shield и т.д.).
    """
    permission_classes = [IsAuthenticated]

    def _has_item(self, inventory, item_id):
        if item_id == 'sword':
            return inventory.has_sword()
        if item_id == 'shield':
            return inventory.has_shield()
        return False

    def _set_crafted_item(self, inventory, item_id):
        if item_id == 'sword':
            inventory.sword_sharpness = 1
        elif item_id == 'shield':
            inventory.shield_durability = 1

    @transaction.atomic
    def post(self, request, item_id):
        if item_id not in ITEM_DISPLAY_NAMES:
            return Response({
                'success': False,
                'error': f'Unknown item_id: {item_id}'
            }, status=status.HTTP_400_BAD_REQUEST)

        recipe = CraftRecipe.objects.filter(item_type=item_id, is_active=True).first()
        if not recipe:
            return Response({
                'success': False,
                'error': f'Recipe for {item_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        inventory = get_or_create_inventory(request.user)

        if self._has_item(inventory, item_id):
            return Response({
                'success': False,
                'error': f'You already have a {item_id}'
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
        self._set_crafted_item(inventory, item_id)
        inventory.save()

        display_name = ITEM_DISPLAY_NAMES[item_id]
        return Response({
            'success': True,
            'message': f'{display_name} crafted successfully',
            'inventory': format_inventory_response(inventory),
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
