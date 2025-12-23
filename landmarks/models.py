from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class PlayerLandmarkObservation(models.Model):
    """
    Модель для хранения факта наблюдения игрока в достопримечательности.
    Хранит только external_id (ID из Wikipedia API), название и описание
    получаются из Unity приложения через Wikipedia API.
    """
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='landmark_observations')
    external_id = models.CharField(max_length=200, help_text="ID достопримечательности из Wikipedia API")
    observed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('player', 'external_id')
        ordering = ['-observed_at']
        indexes = [
            models.Index(fields=['player', 'external_id']),
        ]
    
    def __str__(self):
        return f"{self.player.username} at landmark {self.external_id}"


class LandmarkCapture(models.Model):
    """
    Модель для хранения захвата достопримечательности игроком.
    Хранит информацию о том, кто захватил достопримечательность, когда и какой клан.
    """
    external_id = models.CharField(
        max_length=200, 
        help_text="ID достопримечательности из Wikipedia API",
        db_index=True
    )
    captured_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='landmark_captures',
        verbose_name="Игрок, который захватил"
    )
    clan = models.ForeignKey(
        'clans.Clan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='landmark_captures',
        verbose_name="Клан"
    )
    captured_at = models.DateTimeField(auto_now_add=True, verbose_name="Время захвата")
    
    class Meta:
        verbose_name = "Захват достопримечательности"
        verbose_name_plural = "Захваты достопримечательностей"
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['external_id', '-captured_at']),
            models.Index(fields=['clan']),
        ]
    
    def __str__(self):
        clan_name = self.clan.name if self.clan else "без клана"
        return f"{self.captured_by.username} ({clan_name}) захватил {self.external_id}"
    
    @staticmethod
    def get_latest_capture(external_id):
        """Получает последний захват достопримечательности."""
        try:
            return LandmarkCapture.objects.filter(external_id=external_id).latest('captured_at')
        except LandmarkCapture.DoesNotExist:
            return None
    
    @staticmethod
    def can_capture(external_id):
        """
        Проверяет, можно ли захватить достопримечательность.
        Возвращает (можно_ли_захватить, последний_захват или None).
        """
        latest_capture = LandmarkCapture.get_latest_capture(external_id)
        
        # Если достопримечательность еще никто не захватывал
        if latest_capture is None:
            return True, None
        
        # Проверяем, прошло ли больше часа с последнего захвата
        time_since_capture = timezone.now() - latest_capture.captured_at
        can_capture = time_since_capture >= timedelta(hours=1)
        
        return can_capture, latest_capture
    
    def time_until_next_capture_allowed(self):
        """Возвращает время, через которое можно будет захватить снова (timedelta)."""
        time_since_capture = timezone.now() - self.captured_at
        time_required = timedelta(hours=1)
        remaining = time_required - time_since_capture
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
