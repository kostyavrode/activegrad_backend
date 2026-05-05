from django.urls import path
from .views import (
    InventoryView,
    RecipesView,
    CraftItemView,
    UpgradeSwordView,
    UpgradeShieldView,
    UpgradeCostsView,
)

urlpatterns = [
    path('', InventoryView.as_view(), name='inventory'),
    path('recipes/', RecipesView.as_view(), name='inventory-recipes'),
    path('craft/<str:item_id>/', CraftItemView.as_view(), name='craft-item'),
    path('upgrade/costs/', UpgradeCostsView.as_view(), name='upgrade-costs'),
    path('upgrade/sword/', UpgradeSwordView.as_view(), name='upgrade-sword'),
    path('upgrade/shield/', UpgradeShieldView.as_view(), name='upgrade-shield'),
]
