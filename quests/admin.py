from django.contrib import admin
from .models import Quest, DailyQuest, QuestProgress


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "title", "count", "reward_type", "reward_amount", "is_active", "created_at")
    list_filter = ("type", "reward_type", "is_active", "created_at")
    search_fields = ("title", "description", "type")
    readonly_fields = ("created_at", "updated_at")
    
    def get_fieldsets(self, request, obj=None):
        """Настраиваем fieldsets в зависимости от того, создаем или редактируем объект"""
        if obj is None:
            # При создании нового объекта не показываем системные поля
            return (
                ("Основная информация", {
                    "fields": ("type", "title", "description", "count", "is_active")
                }),
                ("Награда", {
                    "fields": ("reward_type", "reward_amount", "item_id")
                }),
            )
        else:
            # При редактировании показываем системные поля как readonly
            return (
                ("Основная информация", {
                    "fields": ("type", "title", "description", "count", "is_active")
                }),
                ("Награда", {
                    "fields": ("reward_type", "reward_amount", "item_id")
                }),
                ("Системная информация", {
                    "fields": ("created_at", "updated_at"),
                    "classes": ("collapse",)
                }),
            )


@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    list_display = ("user", "quest", "date")
    list_filter = ("date", "quest__type")
    search_fields = ("user__username", "quest__title")
    date_hierarchy = "date"


@admin.register(QuestProgress)
class QuestProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "quest", "current_progress", "is_completed", "reward_claimed", "date")
    list_filter = ("is_completed", "reward_claimed", "date", "quest__type")
    search_fields = ("user__username", "quest__title")
    date_hierarchy = "date"
    readonly_fields = ("created_at", "updated_at")
