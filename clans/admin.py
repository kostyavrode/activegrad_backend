from django.contrib import admin
from .models import Clan


@admin.register(Clan)
class ClanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by', 'created_at', 'get_member_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('created_at',)
    
    def get_member_count(self, obj):
        """Отображает количество участников клана"""
        return obj.get_member_count()
    get_member_count.short_description = 'Участников'

