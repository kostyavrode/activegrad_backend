from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
import random
from .models import Quest, DailyQuest, QuestProgress, QuestPromoCode
from .serializers import QuestSerializer, QuestCompleteSerializer, QuestProgressSerializer, QuestPromoCodeSerializer

User = get_user_model()


class DailyQuestsView(APIView):
    """
    API endpoint для получения ежедневных квестов.
    
    Квесты обновляются каждый день в 00:00 UTC.
    Все квесты должны иметь поле type (не пустое, не null).
    
    **Требования:**
    - Аутентификация обязательна (Bearer token)
    
    **Ответ:**
    - 200 OK: Список квестов с обязательными полями (id, type, title, description, count, reward_type, reward_amount)
    - 400 Bad Request: Недостаточно квестов в базе данных
    - 401 Unauthorized: Требуется аутентификация
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        user = request.user

        # Проверяем существующие квесты на сегодня
        existing_daily_quests = DailyQuest.objects.filter(user=user, date=today)
        
        if existing_daily_quests.exists():
            # Получаем квесты из существующих связей
            quests = [dq.quest for dq in existing_daily_quests.select_related('quest')]
        else:
            # Создаем новые квесты на сегодня
            # Фильтруем только активные квесты с валидным type
            all_quests = list(
                Quest.objects.filter(
                    is_active=True,
                    type__isnull=False
                ).exclude(type='')
            )
            
            if len(all_quests) < 3:
                return Response({
                    "error": "Not enough quests in database. Need at least 3 active quests with valid type."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Выбираем случайные квесты (обычно 3-5)
            num_quests = min(random.randint(3, 5), len(all_quests))
            selected_quests = random.sample(all_quests, num_quests)
            
            # Создаем связи DailyQuest
            for quest in selected_quests:
                DailyQuest.objects.create(user=user, quest=quest, date=today)
            
            quests = selected_quests

        # Сериализуем квесты
        serializer = QuestSerializer(quests, many=True)
        
        # Фильтруем None значения (квесты без type будут None после to_representation)
        quests_data = [q for q in serializer.data if q is not None]
        
        # Дополнительная проверка: убеждаемся что все квесты имеют type
        valid_quests = []
        for quest_data in quests_data:
            if quest_data.get('type') and quest_data['type'].strip() != '':
                valid_quests.append(quest_data)
            else:
                # Логируем проблему (в продакшене можно использовать logger)
                print(f"WARNING: Quest {quest_data.get('id')} has invalid type field")
        
        return Response({
            "quests": valid_quests
        }, status=status.HTTP_200_OK)


class CompleteQuestView(APIView):
    """
    Опциональный API endpoint для подтверждения выполнения квеста.
    Выдает награду пользователю.
    
    **Требования:**
    - Аутентификация обязательна (Bearer token)
    - player_id должен соответствовать текущему пользователю
    - Квест должен быть выполнен (current_progress >= required_count)
    - Награда не должна быть уже получена
    
    **Ответ:**
    - 200 OK: Квест успешно завершен, награда выдана
    - 400 Bad Request: Квест уже завершен или не выполнен
    - 403 Forbidden: player_id не соответствует пользователю
    - 404 Not Found: Квест не найден
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, quest_id):
        serializer = QuestCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        player_id = serializer.validated_data['player_id']
        user = request.user
        
        # Проверяем что player_id соответствует текущему пользователю
        if user.id != player_id:
            return Response({
                "success": False,
                "message": "player_id does not match authenticated user"
            }, status=status.HTTP_403_FORBIDDEN)

        # Получаем квест
        try:
            quest = Quest.objects.get(id=quest_id, is_active=True)
        except Quest.DoesNotExist:
            return Response({
                "success": False,
                "message": "Quest not found"
            }, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        
        # Проверяем, не завершен ли уже квест
        quest_progress, created = QuestProgress.objects.get_or_create(
            user=user,
            quest=quest,
            date=today,
            defaults={'current_progress': 0, 'is_completed': False, 'reward_claimed': False}
        )
        
        if quest_progress.reward_claimed:
            return Response({
                "success": False,
                "message": "Quest already completed and reward claimed"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем выполнение
        if quest_progress.current_progress < quest.count:
            return Response({
                "success": False,
                "message": f"Quest not completed. Progress: {quest_progress.current_progress}/{quest.count}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Выдаем награду
        reward_given = {
            "type": quest.reward_type,
            "amount": quest.reward_amount
        }
        
        level_info = None

        if quest.reward_type == 'coins':
            new_coins = user.add_coins(quest.reward_amount)
            reward_given['new_balance'] = new_coins
        elif quest.reward_type == 'experience':
            exp_result = user.add_experience(quest.reward_amount)
            reward_given['new_experience'] = exp_result['experience']
            if exp_result['leveled_up']:
                level_info = {
                    'new_level': exp_result['level'],
                    'levels_gained': exp_result['levels_gained']
                }
        elif quest.reward_type == 'item':
            # TODO: Логика выдачи предмета по item_id
            pass
        
        # Обновляем пользователя из БД для получения актуальных данных
        user.refresh_from_db()

        # Отмечаем награду как полученную
        quest_progress.reward_claimed = True
        quest_progress.is_completed = True
        quest_progress.save()

        # Сохраняем промокод, если он есть у квеста
        promo_code_issued = None
        if quest.promo_code:
            try:
                promo_code_issued, created = QuestPromoCode.objects.get_or_create(
                    user=user,
                    quest=quest,
                    date=today,
                    promo_code=quest.promo_code,
                    defaults={
                        'quest_progress': quest_progress
                    }
                )
                if not created and not promo_code_issued.quest_progress:
                    # Обновляем связь с quest_progress, если она отсутствует
                    promo_code_issued.quest_progress = quest_progress
                    promo_code_issued.save()
            except Exception as e:
                # Логируем ошибку, но не прерываем выдачу награды
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving promo code for quest {quest.id}: {str(e)}", exc_info=True)

        # Получаем обновленную статистику игрока
        player_stats = {
            "coins": user.coins,
            "experience": user.experience,
            "level": user.level,
            "experience_to_next_level": user.get_experience_to_next_level()
        }
        
        # Формируем сообщение с учетом повышения уровня
        message = "Quest completed successfully"
        if level_info:
            player_stats['level_up'] = level_info
            if level_info['levels_gained'] == 1:
                message = f"Quest completed! Level up! You reached level {level_info['new_level']}!"
            else:
                message = f"Quest completed! Level up! You gained {level_info['levels_gained']} levels and reached level {level_info['new_level']}!"

        response_data = {
            "success": True,
            "message": message,
            "reward_given": reward_given,
            "player_stats": player_stats,
            "level_up_notification": level_info if level_info else None  # Явное уведомление о повышении уровня
        }
        
        # Добавляем промокод в ответ, если он был выдан
        if promo_code_issued:
            response_data["promo_code"] = quest.promo_code

        return Response(response_data, status=status.HTTP_200_OK)


class QuestProgressView(APIView):
    """
    Опциональный API endpoint для получения прогресса квестов пользователя.
    
    Возвращает прогресс всех квестов на текущий день.
    
    **Требования:**
    - Аутентификация обязательна (Bearer token)
    
    **Ответ:**
    - 200 OK: Список прогресса квестов с полями (quest_id, current_progress, required_count, is_completed, reward_claimed)
    - 401 Unauthorized: Требуется аутентификация
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        # Получаем прогресс всех квестов на сегодня
        progress_list = QuestProgress.objects.filter(
            user=user,
            date=today
        ).select_related('quest')
        
        serializer = QuestProgressSerializer(progress_list, many=True)
        
        return Response({
            "quests_progress": serializer.data
        }, status=status.HTTP_200_OK)


class QuestPromoCodesView(APIView):
    """
    API endpoint для получения списка промокодов, полученных игроком за выполнение квестов.
    
    Возвращает промокоды с информацией о квестах (название, описание, картинка).
    
    **Требования:**
    - Аутентификация обязательна (Bearer token)
    
    **Ответ:**
    - 200 OK: Список промокодов с информацией о квестах
    - 401 Unauthorized: Требуется аутентификация
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Получаем все промокоды игрока, отсортированные по дате получения (новые первыми)
        promo_codes = QuestPromoCode.objects.filter(
            user=user
        ).select_related('quest').order_by('-obtained_at')
        
        serializer = QuestPromoCodeSerializer(promo_codes, many=True)
        
        return Response({
            "success": True,
            "promo_codes": serializer.data,
            "total_count": len(serializer.data)
        }, status=status.HTTP_200_OK)
