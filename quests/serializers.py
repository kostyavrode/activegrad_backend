from rest_framework import serializers
from .models import Quest

class QuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quest
        fields = ["id", "title", "description", "count"]
