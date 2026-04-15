import math
from decimal import Decimal

EARTH_RADIUS_KM = 6371.0
NEARBY_RADIUS_KM = 2.0
# ~0.03° широты ≈ 3.3 км — запас для bbox-префильтра
BBOX_DEG_PADDING = 0.03


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние между двумя точками на сфере, километры."""
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return EARTH_RADIUS_KM * c


def bbox_for_point(lat: float, lon: float, pad_deg: float = BBOX_DEG_PADDING):
    """Грубый прямоугольник вокруг точки для префильтра в БД."""
    return {
        "lat_min": max(-90.0, lat - pad_deg),
        "lat_max": min(90.0, lat + pad_deg),
        "lon_min": lon - pad_deg,
        "lon_max": lon + pad_deg,
    }


def decimal_to_float(d: Decimal) -> float:
    return float(d)
