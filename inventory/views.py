import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction

from .models import PlayerInventory, CraftRecipe, UpgradeConfig, UpgradeLevelCost


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


MAX_ITEM_LEVEL = 10

ITEM_DISPLAY = {'sword': 'меча', 'shield': 'щита'}


def _upgrade_item(request, item_type):
    """Общая логика улучшения меча или щита по таблице UpgradeLevelCost."""
    inventory = get_or_create_inventory(request.user)

    if item_type == 'sword':
        if not inventory.has_sword():
            return Response({'success': False, 'error': 'У вас нет меча для улучшения'},
                            status=status.HTTP_400_BAD_REQUEST)
        current_level = inventory.sword_sharpness
    else:
        if not inventory.has_shield():
            return Response({'success': False, 'error': 'У вас нет щита для улучшения'},
                            status=status.HTTP_400_BAD_REQUEST)
        current_level = inventory.shield_durability

    if current_level >= MAX_ITEM_LEVEL:
        return Response({
            'success': False,
            'error': f'Достигнут максимальный уровень {ITEM_DISPLAY[item_type]} ({MAX_ITEM_LEVEL})',
        }, status=status.HTTP_400_BAD_REQUEST)

    next_level = current_level + 1
    cost = UpgradeLevelCost.objects.filter(item_type=item_type, level=next_level).first()
    if not cost:
        return Response({
            'success': False,
            'error': f'Стоимость улучшения до уровня {next_level} не настроена. Обратитесь к администратору.',
        }, status=status.HTTP_400_BAD_REQUEST)

    if (inventory.metal < cost.metal_required or
            inventory.wood < cost.wood_required or
            inventory.blueprints < cost.blueprints_required):
        return Response({
            'success': False,
            'error': 'Insufficient resources',
            'required': {
                'metal': cost.metal_required,
                'wood': cost.wood_required,
                'blueprints': cost.blueprints_required,
            },
            'current': {
                'metal': inventory.metal,
                'wood': inventory.wood,
                'blueprints': inventory.blueprints,
            },
        }, status=status.HTTP_400_BAD_REQUEST)

    inventory.metal -= cost.metal_required
    inventory.wood -= cost.wood_required
    inventory.blueprints -= cost.blueprints_required

    if item_type == 'sword':
        inventory.sword_sharpness = next_level
    else:
        inventory.shield_durability = next_level
    inventory.save()

    return Response({
        'success': True,
        'upgraded': True,
        'new_level': next_level,
        'inventory': format_inventory_response(inventory),
    }, status=status.HTTP_200_OK)


class UpgradeSwordView(APIView):
    """POST /api/inventory/upgrade/sword/ — улучшить меч до следующего уровня."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        return _upgrade_item(request, 'sword')


class UpgradeShieldView(APIView):
    """POST /api/inventory/upgrade/shield/ — улучшить щит до следующего уровня."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        return _upgrade_item(request, 'shield')


_MINIGAME_RESOURCE_TYPES = ('metal', 'wood', 'blueprints')


class MinigameCompleteView(APIView):
    """
    POST /api/inventory/minigame-complete/
    Начисляет ресурсы за прохождение мини-игры в зависимости от результата:
      >= 90% → 2 случайных ресурса
      >= 65% → 1 случайный ресурс
      < 65%  → 0 ресурсов
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            score_percent = int(request.data.get('score_percent', 0))
        except (TypeError, ValueError):
            return Response({'success': False, 'error': 'Invalid score_percent'},
                            status=status.HTTP_400_BAD_REQUEST)

        score_percent = max(0, min(100, score_percent))

        if score_percent >= 90:
            reward_count = 2
        elif score_percent >= 65:
            reward_count = 1
        else:
            reward_count = 0

        resources_gained = {'metal': 0, 'wood': 0, 'blueprints': 0}

        if reward_count > 0:
            inventory = get_or_create_inventory(request.user)
            for _ in range(reward_count):
                chosen = random.choice(_MINIGAME_RESOURCE_TYPES)
                resources_gained[chosen] += 1
            for res, amount in resources_gained.items():
                if amount > 0:
                    setattr(inventory, res, getattr(inventory, res) + amount)
            inventory.save()

        return Response({
            'success': True,
            'score_percent': score_percent,
            'resources_gained': resources_gained,
            'total_resources': reward_count,
        }, status=status.HTTP_200_OK)


class UpgradeCostsView(APIView):
    """
    GET /api/inventory/upgrade/costs/
    Возвращает стоимость следующего улучшения для меча и щита текущего игрока.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory = get_or_create_inventory(request.user)
        result = {}

        for item_type in ('sword', 'shield'):
            if item_type == 'sword':
                current_level = inventory.sword_sharpness
                has_item = inventory.has_sword()
            else:
                current_level = inventory.shield_durability
                has_item = inventory.has_shield()

            if not has_item:
                result[item_type] = {'has_item': False}
                continue

            if current_level >= MAX_ITEM_LEVEL:
                result[item_type] = {
                    'has_item': True,
                    'current_level': current_level,
                    'next_level': None,
                    'requirements': [],
                    'can_upgrade': False,
                    'max_level_reached': True,
                }
                continue

            next_level = current_level + 1
            cost = UpgradeLevelCost.objects.filter(item_type=item_type, level=next_level).first()

            if cost:
                requirements = []
                for rid, field in RESOURCE_FIELDS.items():
                    amount = getattr(cost, f'{rid}_required')
                    if amount > 0:
                        requirements.append({
                            'resource_id': rid,
                            'amount': amount,
                            'display_name': RESOURCE_DISPLAY_NAMES[rid],
                        })
                result[item_type] = {
                    'has_item': True,
                    'current_level': current_level,
                    'next_level': next_level,
                    'requirements': requirements,
                    'can_upgrade': True,
                    'max_level_reached': False,
                }
            else:
                result[item_type] = {
                    'has_item': True,
                    'current_level': current_level,
                    'next_level': None,
                    'requirements': [],
                    'can_upgrade': False,
                    'max_level_reached': False,
                }

        return Response({'success': True, **result}, status=status.HTTP_200_OK)
