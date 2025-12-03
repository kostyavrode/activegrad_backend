from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    coins = models.IntegerField(default=0)  
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
