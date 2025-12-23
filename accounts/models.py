from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone

class CustomUser(AbstractUser):
    coins = models.IntegerField(default=0)  
    experience = models.IntegerField(default=0, help_text="Опыт игрока")
    level = models.IntegerField(default=1, help_text="Уровень игрока")
    registration_date = models.DateTimeField(default=timezone.now)

    boots = models.IntegerField(default=0)
    pants = models.IntegerField(default=0)
    tshirt = models.IntegerField(default=0)
    cap = models.IntegerField(default=0)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    
    # Связь с кланом
    clan = models.ForeignKey(
        'Clan',
        related_name='members',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Клан"
    )
    
    EXPERIENCE_PER_LEVEL = 1000  # Константа: опыта нужно для повышения уровня
    
    def add_coins(self, amount):
        """
        Добавляет монеты пользователю.
        
        Args:
            amount (int): Количество монет для добавления
            
        Returns:
            int: Новый баланс монет
        """
        if amount < 0:
            raise ValueError("Amount must be positive")
        self.coins += amount
        self.save(update_fields=['coins'])
        return self.coins
    
    def add_experience(self, amount):
        """
        Добавляет опыт пользователю и автоматически повышает уровень при достижении 1000 опыта.
        
        Args:
            amount (int): Количество опыта для добавления
            
        Returns:
            dict: Словарь с информацией о результате:
                - 'experience': новый опыт
                - 'level': новый уровень
                - 'leveled_up': True если уровень повысился
        """
        if amount < 0:
            raise ValueError("Amount must be positive")
        
        self.experience += amount
        leveled_up = False
        levels_gained = 0
        
        # Проверяем, нужно ли повысить уровень
        while self.experience >= self.EXPERIENCE_PER_LEVEL:
            self.experience -= self.EXPERIENCE_PER_LEVEL
            self.level += 1
            leveled_up = True
            levels_gained += 1
        
        # Сохраняем изменения
        self.save(update_fields=['experience', 'level'])
        
        return {
            'experience': self.experience,
            'level': self.level,
            'leveled_up': leveled_up,
            'levels_gained': levels_gained
        }
    
    def get_experience_to_next_level(self):
        """
        Возвращает количество опыта, необходимое для следующего уровня.
        
        Returns:
            int: Опыт до следующего уровня
        """
        return self.EXPERIENCE_PER_LEVEL - self.experience
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class FriendRequest(models.Model):
    """
    Модель для запросов дружбы между пользователями.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    from_user = models.ForeignKey(
        CustomUser,
        related_name='sent_friend_requests',
        on_delete=models.CASCADE,
        verbose_name="Отправитель"
    )
    to_user = models.ForeignKey(
        CustomUser,
        related_name='received_friend_requests',
        on_delete=models.CASCADE,
        verbose_name="Получатель"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Запрос дружбы"
        verbose_name_plural = "Запросы дружбы"
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"


class Friendship(models.Model):
    """
    Модель для подтверждённых дружеских отношений.
    Хранит симметричную связь между двумя пользователями.
    """
    user1 = models.ForeignKey(
        CustomUser,
        related_name='friendships_as_user1',
        on_delete=models.CASCADE,
        verbose_name="Пользователь 1"
    )
    user2 = models.ForeignKey(
        CustomUser,
        related_name='friendships_as_user2',
        on_delete=models.CASCADE,
        verbose_name="Пользователь 2"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        verbose_name = "Дружба"
        verbose_name_plural = "Дружбы"
        unique_together = ['user1', 'user2']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user1.username} <-> {self.user2.username}"
    
    @staticmethod
    def are_friends(user1, user2):
        """Проверяет, являются ли два пользователя друзьями."""
        return Friendship.objects.filter(
            (Q(user1=user1) & Q(user2=user2)) |
            (Q(user1=user2) & Q(user2=user1))
        ).exists()
    
    @staticmethod
    def get_friends(user):
        """Получает всех друзей пользователя."""
        friendships = Friendship.objects.filter(
            Q(user1=user) | Q(user2=user)
        )
        friends = []
        for friendship in friendships:
            if friendship.user1 == user:
                friends.append(friendship.user2)
            else:
                friends.append(friendship.user1)
        return friends


class Clan(models.Model):
    """
    Модель для кланов (групп игроков).
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Название клана")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(
        CustomUser,
        related_name='created_clans',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Создатель"
    )
    
    class Meta:
        verbose_name = "Клан"
        verbose_name_plural = "Кланы"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_member_count(self):
        """Возвращает количество участников клана."""
        return self.members.count()
