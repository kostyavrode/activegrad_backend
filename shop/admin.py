from django.contrib import admin
from .models import ShopItem, UserPromoCode, PurchaseHistory


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'promo_code')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'image_url')
        }),
        ('Цена и промокод', {
            'fields': ('price', 'promo_code')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserPromoCode)
class UserPromoCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop_item', 'promo_code', 'purchased_at')
    list_filter = ('purchased_at', 'shop_item')
    search_fields = ('user__username', 'promo_code', 'shop_item__name')
    readonly_fields = ('purchased_at',)
    list_per_page = 50


@admin.register(PurchaseHistory)
class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop_item', 'price_paid', 'promo_code', 'purchased_at')
    list_filter = ('purchased_at', 'shop_item')
    search_fields = ('user__username', 'shop_item__name', 'promo_code')
    readonly_fields = ('purchased_at',)
    list_per_page = 50

