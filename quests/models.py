from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


# Константы для типов квестов
QUEST_TYPE_CHOICES = [
    ('mark_sights', 'Mark Sights'),
    ('visit_sights', 'Visit Sights'),  # Маппится на mark_sights
    ('steps', 'Steps'),
    ('collect_coins', 'Collect Coins'),
    ('level_up', 'Level Up'),
]

# Константы для типов наград
REWARD_TYPE_CHOICES = [
    ('coins', 'Coins'),
    ('experience', 'Experience'),
    ('item', 'Item'),
]


class Quest(models.Model):
    # Обязательные поля
    type = models.CharField(
        max_length=50,
        choices=QUEST_TYPE_CHOICES,
        help_text="Тип условия квеста. КРИТИЧЕСКИ ВАЖНО - не может быть пустым!"
    )
    title = models.CharField(max_length=200, help_text="Название квеста")
    description = models.TextField(max_length=500, help_text="Описание квеста")
    count = models.IntegerField(default=1, help_text="Требуемое количество для выполнения")
    
    # Поля награды
    reward_type = models.CharField(
        max_length=50,
        choices=REWARD_TYPE_CHOICES,
        default='coins',
        help_text="Тип награды: coins, experience, item"
    )
    reward_amount = models.IntegerField(
        default=0,
        help_text="Количество награды (>= 0)"
    )
    item_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID предмета (требуется если reward_type='item')"
    )
    
    # Поля для промокодов и изображений
    promo_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Промокод, который выдается за выполнение квеста"
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL картинки квеста"
    )
    
    # Дополнительные поля
    is_active = models.BooleanField(default=True, help_text="Активен ли квест")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Квест"
        verbose_name_plural = "Квесты"
        ordering = ['-created_at']

    def clean(self):
        """Валидация модели"""
        # Поле type не может быть пустым
        if not self.type or self.type.strip() == '':
            raise ValidationError({'type': 'Поле type не может быть пустым!'})
        
        # count должен быть > 0
        if self.count <= 0:
            raise ValidationError({'count': 'Поле count должно быть больше 0'})
        
        # reward_amount должен быть >= 0
        if self.reward_amount < 0:
            raise ValidationError({'reward_amount': 'Поле reward_amount должно быть >= 0'})
        
        # Если reward_type = 'item', то item_id обязателен
        if self.reward_type == 'item' and not self.item_id:
            raise ValidationError({'item_id': 'Поле item_id обязательно если reward_type="item"'})
        
        # Маппинг visit_sights на mark_sights
        if self.type == 'visit_sights':
            self.type = 'mark_sights'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.type})"


class DailyQuest(models.Model):
    """Связь пользователя с квестом на конкретную дату"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_quests')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        verbose_name = "Ежедневный квест"
        verbose_name_plural = "Ежедневные квесты"
        unique_together = ('user', 'quest', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.quest.title} ({self.date})"


class QuestProgress(models.Model):
    """Прогресс выполнения квеста пользователем"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quest_progresses')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='progresses')
    daily_quest = models.ForeignKey(
        DailyQuest,
        on_delete=models.CASCADE,
        related_name='progresses',
        null=True,
        blank=True
    )
    current_progress = models.IntegerField(default=0, help_text="Текущий прогресс выполнения")
    is_completed = models.BooleanField(default=False, help_text="Выполнен ли квест")
    reward_claimed = models.BooleanField(default=False, help_text="Получена ли награда")
    date = models.DateField(help_text="Дата квеста")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Прогресс квеста"
        verbose_name_plural = "Прогрессы квестов"
        unique_together = ('user', 'quest', 'date')
        ordering = ['-date', '-created_at']

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{self.user.username} - {self.quest.title} {status} ({self.current_progress}/{self.quest.count})"


class QuestPromoCode(models.Model):
    """
    Модель для хранения промокодов, полученных пользователем за выполнение квестов.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quest_promo_codes',
        verbose_name="Пользователь"
    )
    quest = models.ForeignKey(
        Quest,
        on_delete=models.CASCADE,
        related_name='promo_codes_issued',
        verbose_name="Квест"
    )
    promo_code = models.CharField(max_length=100, verbose_name="Промокод")
    quest_progress = models.ForeignKey(
        QuestProgress,
        on_delete=models.SET_NULL,
        related_name='promo_code_issued',
        null=True,
        blank=True,
        verbose_name="Прогресс квеста",
        help_text="Связь с конкретным выполнением квеста"
    )
    date = models.DateField(
        verbose_name="Дата получения",
        help_text="Дата, когда был выполнен квест и получен промокод"
    )
    obtained_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время получения"
    )
    
    class Meta:
        verbose_name = "Промокод за квест"
        verbose_name_plural = "Промокоды за квесты"
        ordering = ['-obtained_at']
        unique_together = ('user', 'quest', 'date', 'promo_code')  # Предотвращает дубликаты
    
    def __str__(self):
        return f"{self.user.username} - {self.promo_code} ({self.quest.title}, {self.date})"