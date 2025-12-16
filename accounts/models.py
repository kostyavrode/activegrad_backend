from django.contrib.auth.models import AbstractUser
from django.db import models
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
