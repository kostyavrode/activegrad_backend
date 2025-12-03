from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Landmark(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    external_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # For external landmark IDs
    
    def __str__(self):
        return self.name or f"Landmark {self.id}"


class PlayerLandmarkObservation(models.Model):
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='landmark_observations')
    landmark = models.ForeignKey(Landmark, on_delete=models.CASCADE, related_name='player_observations')
    observed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('player', 'landmark')
        ordering = ['-observed_at']
    
    def __str__(self):
        return f"{self.player.username} at {self.landmark}"
