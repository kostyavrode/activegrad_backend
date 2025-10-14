from django.urls import path
from .views import DailyQuestsView

urlpatterns = [
    path('daily/', DailyQuestsView.as_view(), name='daily-quests'),
]
