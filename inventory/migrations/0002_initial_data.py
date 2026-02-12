# Data migration: create default CraftRecipe and UpgradeConfig

from django.db import migrations


def create_initial_recipes_and_configs(apps, schema_editor):
    CraftRecipe = apps.get_model('inventory', 'CraftRecipe')
    UpgradeConfig = apps.get_model('inventory', 'UpgradeConfig')

    CraftRecipe.objects.get_or_create(
        item_type='sword',
        defaults={
            'metal_required': 1,
            'wood_required': 1,
            'blueprints_required': 1,
        }
    )
    CraftRecipe.objects.get_or_create(
        item_type='shield',
        defaults={
            'metal_required': 1,
            'wood_required': 1,
            'blueprints_required': 1,
        }
    )

    UpgradeConfig.objects.get_or_create(
        item_type='sword',
        defaults={
            'base_probability': 0,
            'metal_prob_per_unit': 5.0,
            'wood_prob_per_unit': 5.0,
            'blueprints_prob_per_unit': 5.0,
            'max_probability': 95.0,
        }
    )
    UpgradeConfig.objects.get_or_create(
        item_type='shield',
        defaults={
            'base_probability': 0,
            'metal_prob_per_unit': 5.0,
            'wood_prob_per_unit': 5.0,
            'blueprints_prob_per_unit': 5.0,
            'max_probability': 95.0,
        }
    )


def reverse_func(apps, schema_editor):
    CraftRecipe = apps.get_model('inventory', 'CraftRecipe')
    UpgradeConfig = apps.get_model('inventory', 'UpgradeConfig')
    CraftRecipe.objects.all().delete()
    UpgradeConfig.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_recipes_and_configs, reverse_func),
    ]
