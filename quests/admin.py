from django.contrib import admin
from .models import Quest

@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("title", "count", "count")
