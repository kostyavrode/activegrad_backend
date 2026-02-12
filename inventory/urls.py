from django.urls import path
from .views import (
    InventoryView,
    RecipesView,
    CraftSwordView,
    CraftShieldView,
    UpgradeSwordView,
    UpgradeShieldView,
)

urlpatterns = [
    path('', InventoryView.as_view(), name='inventory'),
    path('recipes/', RecipesView.as_view(), name='inventory-recipes'),
    path('craft/sword/', CraftSwordView.as_view(), name='craft-sword'),
    path('craft/shield/', CraftShieldView.as_view(), name='craft-shield'),
    path('upgrade/sword/', UpgradeSwordView.as_view(), name='upgrade-sword'),
    path('upgrade/shield/', UpgradeShieldView.as_view(), name='upgrade-shield'),
]
