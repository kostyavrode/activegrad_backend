from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Clan
from .serializers import ClanSerializer, CreateClanSerializer, JoinClanSerializer

User = get_user_model()


class CreateClanView(APIView):
    """
    API endpoint для создания нового клана.
    POST /api/clans/create/
    Body: {"name": "MyClan", "description": "Описание (опционально)"}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateClanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Проверяем, не состоит ли пользователь уже в каком-то клане
        if user.clan is not None:
            return Response({
                "success": False,
                "error": "You are already in a clan. Leave your current clan first."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Используем транзакцию для атомарности операций
        try:
            with transaction.atomic():
                # Создаем клан
                clan = Clan.objects.create(
                    name=serializer.validated_data['name'],
                    description=serializer.validated_data.get('description', ''),
                    created_by=user
                )
                
                # Обновляем пользователя, присоединяя его к клану
                # Используем update для обхода возможных проблем с кэшированием
                User.objects.filter(id=user.id).update(clan=clan)
                # Обновляем объект user из базы данных
                user.refresh_from_db()
                
            # Перезагружаем клан, чтобы получить актуальные данные
            clan.refresh_from_db()
            
            return Response({
                "success": True,
                "message": "Clan created successfully",
                "clan": ClanSerializer(clan).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Failed to create clan: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JoinClanView(APIView):
    """
    API endpoint для вступления в клан.
    POST /api/clans/join/
    Body: {"clan_id": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = JoinClanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        clan_id = serializer.validated_data['clan_id']
        
        try:
            clan = Clan.objects.get(id=clan_id)
        except Clan.DoesNotExist:
            return Response({
                "success": False,
                "error": "Clan not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, не состоит ли пользователь уже в каком-то клане
        if user.clan is not None:
            if user.clan.id == clan_id:
                return Response({
                    "success": False,
                    "error": "You are already in this clan"
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "success": False,
                    "error": "You are already in another clan. Leave your current clan first."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Присоединяем пользователя к клану
        try:
            with transaction.atomic():
                User.objects.filter(id=user.id).update(clan=clan)
                user.refresh_from_db()
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Failed to join clan: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            "success": True,
            "message": f"You have joined the clan '{clan.name}'",
            "clan": ClanSerializer(clan).data
        }, status=status.HTTP_200_OK)


class LeaveClanView(APIView):
    """
    API endpoint для покидания клана.
    POST /api/clans/leave/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        
        # Проверяем, состоит ли пользователь в клане
        if user.clan is None:
            return Response({
                "success": False,
                "error": "You are not in any clan"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        clan_name = user.clan.name
        clan_id = user.clan.id
        
        # Покидаем клан
        try:
            with transaction.atomic():
                User.objects.filter(id=user.id).update(clan=None)
                user.refresh_from_db()
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Failed to leave clan: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Проверяем, не остался ли клан пустым (если создатель покинул)
        clan = Clan.objects.get(id=clan_id)
        if clan.members.count() == 0:
            # Если клан пуст, удаляем его (или можно оставить, решать вам)
            # Пока оставим клан, но он будет пустым
            pass
        
        return Response({
            "success": True,
            "message": f"You have left the clan '{clan_name}'"
        }, status=status.HTTP_200_OK)


class SearchClansView(APIView):
    """
    API endpoint для поиска кланов.
    GET /api/clans/search/?query=name
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        
        if not query:
            return Response({
                "success": False,
                "error": "Query parameter is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Поиск кланов по названию (без учета регистра)
        clans = Clan.objects.filter(name__icontains=query).order_by('name')[:20]  # Ограничиваем 20 результатами
        
        serializer = ClanSerializer(clans, many=True)
        
        return Response({
            "success": True,
            "clans": serializer.data,
            "total_count": len(serializer.data),
            "query": query
        }, status=status.HTTP_200_OK)


class TopClansView(APIView):
    """
    API endpoint для получения топ-10 лучших кланов.
    GET /api/clans/top/
    
    Рейтинг определяется по количеству участников клана.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Получаем топ-10 кланов по количеству участников
        # Используем annotate для подсчета участников и сортировки
        top_clans = Clan.objects.annotate(
            member_count=Count('members')
        ).filter(member_count__gt=0).order_by('-member_count', '-created_at')[:10]
        
        serializer = ClanSerializer(top_clans, many=True)
        
        return Response({
            "success": True,
            "top_clans": serializer.data,
            "total_count": len(serializer.data)
        }, status=status.HTTP_200_OK)

