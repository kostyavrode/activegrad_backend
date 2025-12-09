from django.urls import path
from .views import (
    ShopItemsListView,
    PurchaseItemView,
    UserPromoCodesView,
    DeletePromoCodeView
)

urlpatterns = [
    path('items/', ShopItemsListView.as_view(), name='shop-items-list'),
    path('purchase/', PurchaseItemView.as_view(), name='purchase-item'),
    path('promo-codes/', UserPromoCodesView.as_view(), name='user-promo-codes'),
    path('promo-codes/delete/<int:promo_code_id>/', DeletePromoCodeView.as_view(), name='delete-promo-code'),
    path('promo-codes/delete/', DeletePromoCodeView.as_view(), name='delete-promo-code-post'),
]

