from django.contrib import admin
from .models import PlayerInventory, CraftRecipe, UpgradeConfig


@admin.register(PlayerInventory)
class PlayerInventoryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'metal', 'wood', 'blueprints',
        'sword_sharpness', 'shield_durability'
    )
    list_filter = ('user',)
    search_fields = ('user__username',)
    readonly_fields = ()


@admin.register(CraftRecipe)
class CraftRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'item_type', 'metal_required', 'wood_required', 'blueprints_required', 'is_active')
    list_filter = ('item_type', 'is_active')
    list_editable = ('metal_required', 'wood_required', 'blueprints_required', 'is_active')


@admin.register(UpgradeConfig)
class UpgradeConfigAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'item_type', 'base_probability',
        'metal_prob_per_unit', 'wood_prob_per_unit', 'blueprints_prob_per_unit',
        'max_probability', 'is_active'
    )
    list_filter = ('item_type', 'is_active')
    list_editable = (
        'base_probability',
        'metal_prob_per_unit', 'wood_prob_per_unit', 'blueprints_prob_per_unit',
        'max_probability', 'is_active'
    )
