from django.urls import path
from .views import DailyQuestsView, CompleteQuestView, QuestProgressView

urlpatterns = [
    path('daily/', DailyQuestsView.as_view(), name='daily-quests'),
    path('<int:quest_id>/complete/', CompleteQuestView.as_view(), name='complete-quest'),
    path('progress/', QuestProgressView.as_view(), name='quest-progress'),
]
