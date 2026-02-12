from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


ITEM_TYPE_CHOICES = [
    ('sword', 'Меч'),
    ('shield', 'Щит'),
]


class PlayerInventory(models.Model):
    """
    Инвентарь игрока: ресурсы и предметы (меч, щит).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='inventory',
        verbose_name='Игрок'
    )
    # Ресурсы
    metal = models.IntegerField(default=0, verbose_name='Металл')
    wood = models.IntegerField(default=0, verbose_name='Дерево')
    blueprints = models.IntegerField(default=0, verbose_name='Чертежи')

    # Предметы (null = ещё не скрафчен)
    sword_sharpness = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Острота меча',
        help_text='Уровень остроты меча. null = меча нет.'
    )
    shield_durability = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name='Стойкость щита',
        help_text='Уровень стойкости щита. null = щита нет.'
    )

    class Meta:
        verbose_name = 'Инвентарь игрока'
        verbose_name_plural = 'Инвентари игроков'

    def __str__(self):
        return f'Инвентарь {self.user.username}'

    def has_sword(self):
        return self.sword_sharpness is not None

    def has_shield(self):
        return self.shield_durability is not None


class CraftRecipe(models.Model):
    """
    Рецепт крафта. Настраивается через админку.
    """
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        unique=True,
        verbose_name='Тип предмета'
    )
    metal_required = models.IntegerField(
        default=1,
        verbose_name='Металл (требуется)'
    )
    wood_required = models.IntegerField(
        default=1,
        verbose_name='Дерево (требуется)'
    )
    blueprints_required = models.IntegerField(
        default=1,
        verbose_name='Чертежи (требуется)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Рецепт крафта'
        verbose_name_plural = 'Рецепты крафта'

    def __str__(self):
        return f'Крафт {self.get_item_type_display()}'

    def get_requirements(self):
        return {
            'metal': self.metal_required,
            'wood': self.wood_required,
            'blueprints': self.blueprints_required,
        }


class UpgradeConfig(models.Model):
    """
    Настройки улучшения предметов. Вероятность успеха зависит от количества ресурсов.
    """
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        unique=True,
        verbose_name='Тип предмета'
    )
    base_probability = models.FloatField(
        default=0.0,
        verbose_name='Базовая вероятность (0-100)',
        help_text='Минимальная вероятность успеха без ресурсов'
    )
    metal_prob_per_unit = models.FloatField(
        default=5.0,
        verbose_name='Вероятность за 1 металл (%)'
    )
    wood_prob_per_unit = models.FloatField(
        default=5.0,
        verbose_name='Вероятность за 1 дерево (%)'
    )
    blueprints_prob_per_unit = models.FloatField(
        default=5.0,
        verbose_name='Вероятность за 1 чертёж (%)'
    )
    max_probability = models.FloatField(
        default=95.0,
        verbose_name='Макс. вероятность (%)',
        help_text='Вероятность не превысит это значение'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Настройка улучшения'
        verbose_name_plural = 'Настройки улучшения'

    def __str__(self):
        return f'Улучшение {self.get_item_type_display()}'

    def calculate_probability(self, metal: int, wood: int, blueprints: int) -> float:
        """Рассчитывает вероятность успеха на основе переданных ресурсов."""
        prob = self.base_probability
        prob += metal * self.metal_prob_per_unit
        prob += wood * self.wood_prob_per_unit
        prob += blueprints * self.blueprints_prob_per_unit
        return min(max(0, prob), self.max_probability)
