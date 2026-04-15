from django.test import TestCase

from .geo import haversine_km, NEARBY_RADIUS_KM


class HaversineTests(TestCase):
    def test_same_point_zero_km(self):
        self.assertAlmostEqual(haversine_km(55.75, 37.62, 55.75, 37.62), 0.0, places=5)

    def test_short_distance_reasonable(self):
        # ~1 км по параллели в средних широтах
        d = haversine_km(55.75, 37.62, 55.759, 37.62)
        self.assertLess(d, NEARBY_RADIUS_KM)
