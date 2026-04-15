import logging
import random
from typing import Any, Dict, Optional

from django.utils import timezone

from quests.models import DailyQuest, QuestProgress
from inventory.views import get_or_create_inventory

logger = logging.getLogger(__name__)

REWARD_MIN = 0
REWARD_MAX = 10


def apply_mark_sights_progress_and_inventory_rewards(
    player, newly_created_count: int, *, player_id_for_log: int | None = None
) -> Optional[Dict[str, Any]]:
    """
    Обновляет прогресс ежедневных квестов типа mark_sights и выдаёт ресурсы инвентаря
    за новые отметки (metal, wood, blueprints: 0–10 на каждую отметку, суммарно).

    Возвращает словарь resources_gained при успешной выдаче ресурсов, иначе None
    (квесты могли обновиться даже если инвентарь упал с ошибкой).
    """
    if newly_created_count <= 0:
        return None

    pid = player_id_for_log if player_id_for_log is not None else player.id

    try:
        today = timezone.now().date()
        daily_quests = DailyQuest.objects.filter(
            user=player,
            date=today,
            quest__type="mark_sights",
            quest__is_active=True,
        ).select_related("quest")

        for daily_quest in daily_quests:
            quest = daily_quest.quest
            quest_progress, created = QuestProgress.objects.get_or_create(
                user=player,
                quest=quest,
                date=today,
                defaults={
                    "current_progress": 0,
                    "is_completed": False,
                    "reward_claimed": False,
                    "daily_quest": daily_quest,
                },
            )
            if not created and not quest_progress.daily_quest:
                quest_progress.daily_quest = daily_quest

            new_progress = min(
                quest_progress.current_progress + newly_created_count,
                quest.count,
            )
            quest_progress.current_progress = new_progress
            if new_progress >= quest.count:
                quest_progress.is_completed = True
            quest_progress.save()

            logger.info(
                "Updated quest progress for player %s, quest %s: %s/%s",
                pid,
                quest.id,
                quest_progress.current_progress,
                quest.count,
            )
    except Exception:
        logger.error(
            "Error updating quest progress for player %s",
            pid,
            exc_info=True,
        )

    resources_gained = None
    try:
        total_metal = sum(
            random.randint(REWARD_MIN, REWARD_MAX) for _ in range(newly_created_count)
        )
        total_wood = sum(
            random.randint(REWARD_MIN, REWARD_MAX) for _ in range(newly_created_count)
        )
        total_blueprints = sum(
            random.randint(REWARD_MIN, REWARD_MAX) for _ in range(newly_created_count)
        )
        inventory = get_or_create_inventory(player)
        inventory.metal += total_metal
        inventory.wood += total_wood
        inventory.blueprints += total_blueprints
        inventory.save()
        resources_gained = {
            "metal": total_metal,
            "wood": total_wood,
            "blueprints": total_blueprints,
        }
        logger.info(
            "Player %s received resources for %s new mark(s): metal=%s wood=%s blueprints=%s",
            pid,
            newly_created_count,
            total_metal,
            total_wood,
            total_blueprints,
        )
    except Exception:
        logger.error(
            "Error granting resources for player %s",
            pid,
            exc_info=True,
        )

    return resources_gained
