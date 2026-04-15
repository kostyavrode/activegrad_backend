import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from landmarks.mark_sights_rewards import apply_mark_sights_progress_and_inventory_rewards

from .geo import (
    bbox_for_point,
    decimal_to_float,
    haversine_km,
    NEARBY_RADIUS_KM,
)
from .models import PartnerStore, PlayerPartnerStoreObservation
from .serializers import SavePlayerPartnerStoresSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class NearbyPartnerStoresView(APIView):
    """
    GET: активные магазины партнёров в радиусе 2 км от переданных координат.
    Query: latitude, longitude
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat_raw = request.query_params.get("latitude")
        lon_raw = request.query_params.get("longitude")
        if lat_raw is None or lon_raw is None:
            return Response(
                {
                    "success": False,
                    "error": "latitude and longitude are required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
        except (TypeError, ValueError):
            return Response(
                {
                    "success": False,
                    "error": "latitude and longitude must be valid numbers",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            return Response(
                {
                    "success": False,
                    "error": "latitude must be in [-90, 90], longitude in [-180, 180]",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        box = bbox_for_point(lat, lon)
        qs = (
            PartnerStore.objects.filter(
                is_active=True,
                latitude__gte=box["lat_min"],
                latitude__lte=box["lat_max"],
                longitude__gte=box["lon_min"],
                longitude__lte=box["lon_max"],
            )
            .prefetch_related("tags")
            .only(
                "id",
                "name",
                "address",
                "image_url",
                "latitude",
                "longitude",
            )
        )

        with_tags = []
        for store in qs:
            slat = decimal_to_float(store.latitude)
            slon = decimal_to_float(store.longitude)
            dist = haversine_km(lat, lon, slat, slon)
            if dist <= NEARBY_RADIUS_KM:
                tag_names = [t.name for t in store.tags.all()]
                with_tags.append(
                    (
                        dist,
                        {
                            "id": store.id,
                            "name": store.name,
                            "address": store.address,
                            "image_url": store.image_url,
                            "latitude": slat,
                            "longitude": slon,
                            "distance_km": round(dist, 6),
                            "tags": tag_names,
                        },
                    )
                )

        with_tags.sort(key=lambda x: x[0])
        stores_payload = [item[1] for item in with_tags]

        return Response(
            {
                "success": True,
                "latitude": lat,
                "longitude": lon,
                "radius_km": NEARBY_RADIUS_KM,
                "stores": stores_payload,
                "total_count": len(stores_payload),
            },
            status=status.HTTP_200_OK,
        )


class SavePlayerPartnerStoresView(APIView):
    """
    POST: сохранить отметки посещения магазинов партнёров (как landmarks/save/).
    Body: player_id, store_ids (список PK PartnerStore).
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            serializer = SavePlayerPartnerStoresSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(
                    "Invalid partner store save payload: %s", serializer.errors
                )
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            player_id = serializer.validated_data["player_id"]
            store_ids = serializer.validated_data["store_ids"]

            if request.user.id != player_id:
                return Response(
                    {
                        "success": False,
                        "error": "player_id must match the authenticated user",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            try:
                player = User.objects.get(id=player_id)
            except User.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "error": f"Player with ID {player_id} not found",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            valid_stores = PartnerStore.objects.filter(
                id__in=store_ids,
                is_active=True,
            )
            valid_by_id = {s.id: s for s in valid_stores}

            saved_store_ids = []
            newly_created_count = 0

            for sid in store_ids:
                store = valid_by_id.get(sid)
                if not store:
                    continue
                try:
                    _, created = PlayerPartnerStoreObservation.objects.get_or_create(
                        player=player,
                        partner_store=store,
                    )
                    if created:
                        saved_store_ids.append(sid)
                        newly_created_count += 1
                except IntegrityError:
                    logger.error(
                        "IntegrityError saving partner store observation player=%s store=%s",
                        player_id,
                        sid,
                        exc_info=True,
                    )
                    continue

            resources_gained = None
            if newly_created_count > 0:
                resources_gained = apply_mark_sights_progress_and_inventory_rewards(
                    player,
                    newly_created_count,
                    player_id_for_log=player_id,
                )

            response_data = {
                "success": True,
                "message": f"Successfully saved {len(saved_store_ids)} partner store observation(s)",
                "player_id": player_id,
                "saved_store_ids": saved_store_ids,
                "total_saved": len(saved_store_ids),
            }
            if resources_gained:
                response_data["resources_gained"] = resources_gained

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                "Unexpected error in SavePlayerPartnerStoresView: %s",
                e,
                exc_info=True,
            )
            return Response(
                {
                    "success": False,
                    "error": "Internal server error",
                    "message": str(e) if hasattr(e, "__str__") else "Unknown error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetPlayerPartnerStoresView(APIView):
    """GET: список id магазинов партнёров, где побывал игрок."""

    permission_classes = [IsAuthenticated]

    def get(self, request, player_id=None):
        player_id = player_id or request.query_params.get("player_id")

        if not player_id:
            return Response(
                {"success": False, "error": "player_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            player_id = int(player_id)
        except (ValueError, TypeError):
            return Response(
                {"success": False, "error": "player_id must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            player = User.objects.get(id=player_id)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": f"Player with ID {player_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        observations = PlayerPartnerStoreObservation.objects.filter(
            player=player
        ).select_related("partner_store")
        store_ids = [obs.partner_store_id for obs in observations]

        return Response(
            {
                "success": True,
                "player_id": player.id,
                "player_username": player.username,
                "store_ids": store_ids,
                "total_count": len(store_ids),
            },
            status=status.HTTP_200_OK,
        )
