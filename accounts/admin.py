from django.contrib import admin
from .models import CustomUser, FriendRequest, Friendship, Clan


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'level', 'coins', 'experience', 'clan', 'registration_date')
    list_filter = ('level', 'gender', 'registration_date', 'clan')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'clan__name')


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user1__username', 'user2__username')
    readonly_fields = ('created_at',)


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
