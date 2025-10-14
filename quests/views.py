from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import random
from .models import Quest, DailyQuest
from .serializers import QuestSerializer

class DailyQuestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        user = request.user

        existing_quests = DailyQuest.objects.filter(user=user, date=today)
        if existing_quests.exists():
            quests = [dq.quest for dq in existing_quests]
        else:
            all_quests = list(Quest.objects.all())
            if len(all_quests) < 3:
                return Response({"error": "Not enough quests in database."}, status=400)
            selected_quests = random.sample(all_quests, 3)
            for q in selected_quests:
                DailyQuest.objects.create(user=user, quest=q, date=today)
            quests = selected_quests

        serializer = QuestSerializer(quests, many=True)
        return Response({"quests": serializer.data})
