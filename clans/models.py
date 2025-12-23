from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Clan(models.Model):
    """
    Модель для кланов (групп игроков).
    """
    FORBIDDEN_CHARS = ['<', '>', '"', "'", '&', '/', '\\', '{', '}', '[', ']', '|', '*', '?', '%', '$', '#', '@', '!', '`']
    
    name = models.CharField(max_length=20, unique=True, verbose_name="Название клана")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(
        User,
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
    
    def get_captured_landmarks_count(self):
        """Возвращает количество захваченных достопримечательностей кланом."""
        try:
            from landmarks.models import LandmarkCapture
            # Получаем уникальные external_id захваченных достопримечательностей кланом
            unique_captures = LandmarkCapture.objects.filter(
                clan=self
            ).values('external_id').distinct().count()
            return unique_captures
        except Exception:
            return 0
    
    @staticmethod
    def validate_clan_name(name):
        """
        Валидирует название клана.
        Проверяет длину и запрещенные символы.
        """
        if not name or not name.strip():
            raise ValueError("Название клана не может быть пустым")
        
        name = name.strip()
        
        if len(name) > 20:
            raise ValueError("Название клана не может быть длиннее 20 символов")
        
        for char in Clan.FORBIDDEN_CHARS:
            if char in name:
                raise ValueError(f"Название клана не может содержать символ '{char}'")
        
        return name

