import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
import logging
from .models import PlayerLandmarkObservation, LandmarkCapture, LandmarkCaptureCooldown, LandmarkCaptureRewardCollection
from .serializers import SavePlayerLandmarksSerializer, CaptureLandmarkSerializer, LandmarkCaptureSerializer
from .mark_sights_rewards import apply_mark_sights_progress_and_inventory_rewards
from inventory.views import get_or_create_inventory

User = get_user_model()


def calculate_capture_probability(attacker_sword_level: int, defender_shield_level: int) -> float:
    """
    Вероятность успешного захвата в зависимости от уровня меча атакующего и щита защитника.
    diff = attacker_sword - defender_shield
    diff >= 2: 100%
    diff == 1: 80%
    diff == 0: 50%
    diff == -1: 25%
    diff <= -2: 5%
    """
    diff = attacker_sword_level - defender_shield_level
    if diff >= 2:
        return 100.0
    if diff == 1:
        return 80.0
    if diff == 0:
        return 50.0
    if diff == -1:
        return 25.0
    return 5.0  # diff <= -2

logger = logging.getLogger(__name__)


class SavePlayerLandmarksView(APIView):
    """
    API endpoint для сохранения факта того, что игрок был в достопримечательности.
    Принимает player_id и список external_ids (ID из Wikipedia API).
    Названия и описания достопримечательностей получаются из Unity через Wikipedia API.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            serializer = SavePlayerLandmarksSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Invalid serializer data: {serializer.errors}")
                return Response({
                    "success": False,
                    "errors": serializer.errors
                }, status=400)

            player_id = serializer.validated_data['player_id']
            external_ids = serializer.validated_data['external_ids']

            # Получаем игрока
            try:
                player = User.objects.get(id=player_id)
            except User.DoesNotExist:
                logger.warning(f"Player with ID {player_id} not found")
                return Response({
                    "success": False,
                    "error": f"Player with ID {player_id} not found"
                }, status=404)

            # Сохраняем наблюдения (unique_together предотвращает дубликаты)
            saved_external_ids = []
            newly_created_count = 0
            
            for external_id in external_ids:
                try:
                    # Преобразуем в строку на случай, если пришло число
                    external_id = str(external_id).strip()
                    if not external_id:
                        continue
                        
                    # Создаем или получаем наблюдение (unique_together предотвращает дубликаты)
                    observation, created = PlayerLandmarkObservation.objects.get_or_create(
                        player=player,
                        external_id=external_id
                    )
                    if created:
                        saved_external_ids.append(external_id)
                        newly_created_count += 1
                except IntegrityError as e:
                    logger.error(f"IntegrityError for external_id {external_id}: {str(e)}")
                    # Пропускаем этот external_id и продолжаем
                    continue
                except Exception as e:
                    logger.error(f"Error saving external_id {external_id}: {str(e)}")
                    # Пропускаем этот external_id и продолжаем
                    continue

            resources_gained = None
            if newly_created_count > 0:
                resources_gained = apply_mark_sights_progress_and_inventory_rewards(
                    player,
                    newly_created_count,
                    player_id_for_log=player_id,
                )

            response_data = {
                "success": True,
                "message": f"Successfully saved {len(saved_external_ids)} landmark observation(s)",
                "player_id": player_id,
                "saved_external_ids": saved_external_ids,
                "total_saved": len(saved_external_ids)
            }
            if resources_gained:
                response_data["resources_gained"] = resources_gained

            return Response(response_data, status=200)
            
        except Exception as e:
            logger.error(f"Unexpected error in SavePlayerLandmarksView: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": "Internal server error",
                "message": str(e) if hasattr(e, '__str__') else "Unknown error"
            }, status=500)


class GetPlayerLandmarksView(APIView):
    """
    API endpoint для получения списка ID достопримечательностей, где был игрок.
    Принимает player_id как query параметр или в URL path.
    Возвращает список external_ids (ID из Wikipedia API).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None):
        # Получаем player_id из URL path или query параметра
        player_id = player_id or request.query_params.get('player_id')
        
        if not player_id:
            return Response({
                "success": False,
                "error": "player_id is required"
            }, status=400)

        try:
            player_id = int(player_id)
        except (ValueError, TypeError):
            return Response({
                "success": False,
                "error": "player_id must be a valid integer"
            }, status=400)

        # Получаем игрока
        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": f"Player with ID {player_id} not found"
            }, status=404)

        # Получаем все наблюдения игрока
        observations = PlayerLandmarkObservation.objects.filter(player=player)
        external_ids = [obs.external_id for obs in observations]
        
        return Response({
            "success": True,
            "player_id": player.id,
            "player_username": player.username,
            "external_ids": external_ids,
            "total_count": len(external_ids)
        }, status=200)


class TestLandmarksView(APIView):
    """Тестовый endpoint для проверки доступности landmarks API"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "status": "OK",
            "message": "Landmarks API is working",
            "user": request.user.username,
            "user_id": request.user.id
        }, status=200)
    
    def post(self, request):
        return Response({
            "status": "OK",
            "message": "Landmarks API POST is working",
            "user": request.user.username,
            "user_id": request.user.id,
            "received_data": request.data
        }, status=200)


class CaptureLandmarkView(APIView):
    """
    Метод 2: Захват достопримечательности.
    POST /api/landmarks/capture/
    Body: {"external_id": "12345"}
    
    Логика:
    - Проверяет can_capture_now через метод can_capture()
    - Если можно - создает новую запись захвата (меняет владельца)
    - Если нельзя - возвращает ошибку
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CaptureLandmarkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        external_id = serializer.validated_data['external_id']
        user = request.user
        
        # Меч обязателен для захвата
        attacker_inv = get_or_create_inventory(user)
        if not attacker_inv.has_sword():
            return Response({
                "success": False,
                "error": "Sword required",
                "message": "Для захвата достопримечательности нужен меч. Скрафтите меч в инвентаре.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, можно ли захватить (30 мин неприступности или 5 мин после неудачи)
        can_capture_now, latest_capture, fail_cooldown = LandmarkCapture.can_capture(external_id)

        if not can_capture_now:
            if fail_cooldown:
                # Блокировка из-за неудачной попытки (5 мин)
                time_remaining = fail_cooldown.time_remaining()
                minutes_remaining = int(time_remaining.total_seconds() / 60)
                seconds_remaining = int(time_remaining.total_seconds() % 60)
                return Response({
                    "success": False,
                    "error": "Landmark cannot be captured now",
                    "message": f"Последняя попытка захвата не удалась. Повторная попытка возможна через {minutes_remaining} мин {seconds_remaining} сек",
                    "can_capture_now": False,
                    "block_reason": "failed_capture_cooldown",
                    "time_until_next_capture_minutes": minutes_remaining,
                    "time_until_next_capture_seconds": seconds_remaining,
                    "current_owner": {
                        "id": latest_capture.captured_by.id,
                        "username": latest_capture.captured_by.username
                    } if latest_capture else None,
                    "captured_at": latest_capture.captured_at.isoformat() if latest_capture else None,
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Блокировка из-за 30-минутной неприступности
                time_remaining = latest_capture.time_until_next_capture_allowed()
                minutes_remaining = int(time_remaining.total_seconds() / 60)
                seconds_remaining = int(time_remaining.total_seconds() % 60)
                return Response({
                    "success": False,
                    "error": "Landmark cannot be captured now",
                    "message": f"Достопримечательность под защитой. Попытка перехвата возможна через {minutes_remaining} мин {seconds_remaining} сек",
                    "can_capture_now": False,
                    "block_reason": "invulnerability",
                    "current_owner": {
                        "id": latest_capture.captured_by.id,
                        "username": latest_capture.captured_by.username
                    },
                    "captured_at": latest_capture.captured_at.isoformat(),
                    "time_until_next_capture_minutes": minutes_remaining,
                    "time_until_next_capture_seconds": seconds_remaining,
                }, status=status.HTTP_400_BAD_REQUEST)
        
        attacker_sword = attacker_inv.sword_sharpness

        # Нельзя захватить достопримечательность у самого себя
        if latest_capture is not None and latest_capture.captured_by == user:
            return Response({
                "success": False,
                "error": "Already owner",
                "message": "Вы уже владеете этой достопримечательностью. Нельзя захватить её у самого себя.",
                "is_owner": True,
                "captured_at": latest_capture.captured_at.isoformat(),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Первый захват (никто не владел) — всегда успех
        if latest_capture is None:
            capture_succeeded = True
            probability = 100.0
        else:
            # Перехват — считаем вероятность по мечу атакующего и щиту защитника
            defender = latest_capture.captured_by
            defender_inv = get_or_create_inventory(defender)
            defender_shield = defender_inv.shield_durability if defender_inv.shield_durability is not None else 0

            probability = calculate_capture_probability(attacker_sword, defender_shield)
            roll = random.uniform(0, 100)
            capture_succeeded = roll < probability

        if not capture_succeeded:
            # Кулдаун 5 минут — нельзя пытаться снова
            cooldown_until = timezone.now() + timedelta(minutes=LandmarkCapture.FAILED_CAPTURE_COOLDOWN_MINUTES)
            LandmarkCaptureCooldown.objects.update_or_create(
                external_id=external_id,
                defaults={"cooldown_until": cooldown_until}
            )
            time_remaining = cooldown_until - timezone.now()
            return Response({
                "success": False,
                "error": "Capture failed",
                "message": "Захват не удался. Повторная попытка возможна через 5 минут.",
                "capture_failed": True,
                "probability": round(probability, 2),
                "roll": round(roll, 2),
                "attacker_sword_level": attacker_sword,
                "defender_shield_level": defender_shield,
                "retry_available_in_minutes": 5,
                "retry_available_in_seconds": int(time_remaining.total_seconds()),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Захват успешен — создаём новую запись
        new_capture = LandmarkCapture.objects.create(
            external_id=external_id,
            captured_by=user,
            clan=user.clan
        )

        # Бонус за захват: 1 случайный ресурс сразу
        capture_resource = random.choice(('metal', 'wood', 'blueprints'))
        setattr(attacker_inv, capture_resource, getattr(attacker_inv, capture_resource) + 1)
        attacker_inv.save()
        capture_reward = {capture_resource: 1}

        return Response({
            "success": True,
            "message": "Достопримечательность захвачена!",
            "capture": {
                "id": new_capture.id,
                "external_id": new_capture.external_id,
                "captured_by": {
                    "id": new_capture.captured_by.id,
                    "username": new_capture.captured_by.username
                },
                "captured_at": new_capture.captured_at.isoformat(),
                "clan": {
                    "id": new_capture.clan.id,
                    "name": new_capture.clan.name
                } if new_capture.clan else None
            },
            "capture_reward": capture_reward,
        }, status=status.HTTP_201_CREATED)


class CollectCaptureRewardsView(APIView):
    """
    POST /api/landmarks/collect-rewards/
    Собирает накопленные почасовые ресурсы за все захваченные игроком достопримечательности.
    1 случайный ресурс за каждый целый час владения, максимум 8 часов на одну точку.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        now = timezone.now()

        # Все external_id, когда-либо захваченные игроком
        user_external_ids = (
            LandmarkCapture.objects.filter(captured_by=user)
            .values_list('external_id', flat=True)
            .distinct()
        )

        total_resources = {'metal': 0, 'wood': 0, 'blueprints': 0}
        total_hours_collected = 0

        for external_id in user_external_ids:
            latest = LandmarkCapture.get_latest_capture(external_id)
            # Пропускаем, если игрок больше не владеет точкой
            if latest is None or latest.captured_by_id != user.id:
                continue

            elapsed_seconds = (now - latest.captured_at).total_seconds()

            # Точка приносит ресурсы только первые 8 часов с момента захвата
            if elapsed_seconds >= LandmarkCaptureRewardCollection.MAX_REWARD_HOURS * 3600:
                continue

            whole_hours = int(elapsed_seconds // 3600)
            if whole_hours == 0:
                continue

            collection, _ = LandmarkCaptureRewardCollection.objects.get_or_create(capture=latest)
            available = max(0, whole_hours - collection.hours_collected)
            if available == 0:
                continue

            for _ in range(available):
                chosen = random.choice(('metal', 'wood', 'blueprints'))
                total_resources[chosen] += 1

            collection.hours_collected = whole_hours
            collection.save()
            total_hours_collected += available

        if total_hours_collected == 0:
            return Response({
                "success": True,
                "message": "Нет доступных ресурсов для сбора.",
                "resources_gained": {"metal": 0, "wood": 0, "blueprints": 0},
                "total_hours": 0,
            })

        inventory = get_or_create_inventory(user)
        inventory.metal += total_resources['metal']
        inventory.wood += total_resources['wood']
        inventory.blueprints += total_resources['blueprints']
        inventory.save()

        logger.info(
            "Player %s collected capture rewards: %s (total hours: %s)",
            user.id, total_resources, total_hours_collected,
        )

        return Response({
            "success": True,
            "message": f"Собрано ресурсов за {total_hours_collected} ч. владения.",
            "resources_gained": total_resources,
            "total_hours": total_hours_collected,
        })


class GetLandmarkCaptureView(APIView):
    """
    Метод 1: Получение информации о захвате достопримечательности.
    GET /api/landmarks/<external_id>/capture/
    
    Возвращает:
    - Кто захватил (captured_by)
    - Когда захватил (captured_at)
    - Клан (clan)
    - can_capture_now (булевое значение - можно ли захватить сейчас)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, external_id):
        # Получаем последний захват
        latest_capture = LandmarkCapture.get_latest_capture(external_id)

        # Проверяем, можно ли захватить (30 мин или 5 мин после неудачи)
        can_capture_now, _, fail_cooldown = LandmarkCapture.can_capture(external_id)

        # Меч атакующего (текущего пользователя)
        attacker_inv = get_or_create_inventory(request.user)
        attacker_sword = attacker_inv.sword_sharpness if attacker_inv.sword_sharpness is not None else 0

        # Если достопримечательность еще не захватывалась — вероятность 100%
        if latest_capture is None:
            return Response({
                "success": True,
                "captured": False,
                "can_capture_now": not fail_cooldown,
                "captured_by": None,
                "captured_at": None,
                "clan": None,
                "defender_shield_level": None,
                "capture_probability": 100,
            }, status=status.HTTP_200_OK)

        # Уровень щита текущего владельца (для отображения в UI)
        defender_inv = get_or_create_inventory(latest_capture.captured_by)
        defender_shield = defender_inv.shield_durability if defender_inv.shield_durability is not None else 0

        capture_probability = int(calculate_capture_probability(attacker_sword, defender_shield))

        response_data = {
            "success": True,
            "captured": True,
            "can_capture_now": can_capture_now,
            "captured_by": {
                "id": latest_capture.captured_by.id,
                "username": latest_capture.captured_by.username
            },
            "captured_at": latest_capture.captured_at.isoformat(),
            "clan": {
                "id": latest_capture.clan.id,
                "name": latest_capture.clan.name
            } if latest_capture.clan else None,
            "defender_shield_level": defender_shield,
            "capture_probability": capture_probability,
        }
        if not can_capture_now:
            if fail_cooldown:
                time_remaining = fail_cooldown.time_remaining()
            else:
                time_remaining = latest_capture.time_until_next_capture_allowed()
            response_data["time_until_next_capture_minutes"] = int(time_remaining.total_seconds() / 60)
            response_data["time_until_next_capture_seconds"] = int(time_remaining.total_seconds() % 60)
            response_data["block_reason"] = "failed_capture_cooldown" if fail_cooldown else "invulnerability"
        return Response(response_data, status=status.HTTP_200_OK)
