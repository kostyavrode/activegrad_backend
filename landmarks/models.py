from django.db import models
from django.contrib.auth import get_user_model

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
