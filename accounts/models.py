from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    coins = models.IntegerField(default=0)  
    registration_date = models.DateTimeField(default=timezone.now)

    # одежда (id предмета, 0 = нет одежды)
    boots = models.IntegerField(default=0)
    pants = models.IntegerField(default=0)
    tshirt = models.IntegerField(default=0)
    cap = models.IntegerField(default=0)
