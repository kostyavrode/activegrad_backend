from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Quest(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=300)
    count = models.IntegerField(default=1)

    def __str__(self):
        return self.title


class DailyQuest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_quests')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = ('user', 'quest', 'date')
