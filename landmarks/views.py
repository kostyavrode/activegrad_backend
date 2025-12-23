from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
import logging
from .models import PlayerLandmarkObservation, LandmarkCapture
from .serializers import SavePlayerLandmarksSerializer, CaptureLandmarkSerializer, LandmarkCaptureSerializer
from quests.models import Quest, QuestProgress, DailyQuest

User = get_user_model()
logger = logging.getLogger(__name__)


class SavePlayerLandmarksView(APIView):
    """
    API endpoint для сохранения факта того, что игрок был в достопримечательности.
    Принимает player_id и список external_ids (ID из Wikipedia API).
    Названия и описания достопримечательностей получаются из Unity через Wikipedia API.
    """
    permission_classes = [IsAuthenticated]

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

            # Обновляем прогресс квестов типа 'mark_sights'
            if newly_created_count > 0:
                try:
                    today = timezone.now().date()
                    
                    # Находим все активные квесты типа 'mark_sights' для игрока
                    # Получаем квесты через DailyQuest для текущей даты
                    daily_quests = DailyQuest.objects.filter(
                        user=player,
                        date=today,
                        quest__type='mark_sights',
                        quest__is_active=True
                    ).select_related('quest')
                    
                    # Обновляем прогресс для каждого квеста
                    for daily_quest in daily_quests:
                        quest = daily_quest.quest
                        
                        # Получаем или создаем QuestProgress
                        quest_progress, created = QuestProgress.objects.get_or_create(
                            user=player,
                            quest=quest,
                            date=today,
                            defaults={
                                'current_progress': 0,
                                'is_completed': False,
                                'reward_claimed': False,
                                'daily_quest': daily_quest
                            }
                        )
                        
                        # Если QuestProgress уже существовал, обновляем daily_quest если нужно
                        if not created and not quest_progress.daily_quest:
                            quest_progress.daily_quest = daily_quest
                        
                        # Увеличиваем прогресс (но не больше требуемого количества)
                        new_progress = min(
                            quest_progress.current_progress + newly_created_count,
                            quest.count
                        )
                        quest_progress.current_progress = new_progress
                        
                        # Проверяем, выполнен ли квест
                        if new_progress >= quest.count:
                            quest_progress.is_completed = True
                        
                        quest_progress.save()
                        
                        logger.info(
                            f"Updated quest progress for player {player_id}, "
                            f"quest {quest.id}: {quest_progress.current_progress}/{quest.count}"
                        )
                        
                except Exception as e:
                    # Логируем ошибку, но не прерываем сохранение достопримечательностей
                    logger.error(
                        f"Error updating quest progress for player {player_id}: {str(e)}",
                        exc_info=True
                    )

            return Response({
                "success": True,
                "message": f"Successfully saved {len(saved_external_ids)} landmark observation(s)",
                "player_id": player_id,
                "saved_external_ids": saved_external_ids,
                "total_saved": len(saved_external_ids)
            }, status=200)
            
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
        
        # Проверяем, можно ли захватить достопримечательность сейчас
        can_capture_now, latest_capture = LandmarkCapture.can_capture(external_id)
        
        if not can_capture_now:
            # Вычисляем оставшееся время
            time_remaining = latest_capture.time_until_next_capture_allowed()
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            seconds_remaining = int(time_remaining.total_seconds() % 60)
            
            return Response({
                "success": False,
                "error": "Landmark cannot be captured now",
                "message": f"Нельзя захватить достопримечательность сейчас. Повторный захват возможен через {minutes_remaining} мин {seconds_remaining} сек",
                "can_capture_now": False,
                "current_owner": {
                    "id": latest_capture.captured_by.id,
                    "username": latest_capture.captured_by.username
                },
                "captured_at": latest_capture.captured_at.isoformat(),
                "time_until_next_capture_minutes": minutes_remaining,
                "time_until_next_capture_seconds": seconds_remaining,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Создаем новый захват (меняем владельца)
        new_capture = LandmarkCapture.objects.create(
            external_id=external_id,
            captured_by=user,
            clan=user.clan  # Клан игрока (может быть None)
        )
        
        return Response({
            "success": True,
            "message": "Landmark captured successfully. Owner changed.",
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
            }
        }, status=status.HTTP_201_CREATED)


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
        
        # Проверяем, можно ли захватить сейчас
        can_capture_now, _ = LandmarkCapture.can_capture(external_id)
        
        # Если достопримечательность еще не захватывалась
        if latest_capture is None:
            return Response({
                "success": True,
                "captured": False,
                "can_capture_now": True,
                "captured_by": None,
                "captured_at": None,
                "clan": None
            }, status=status.HTTP_200_OK)
        
        # Если захватывалась - возвращаем информацию о текущем владельце
        return Response({
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
            } if latest_capture.clan else None
        }, status=status.HTTP_200_OK)
