from django.db import migrations

# Стоимость по умолчанию для уровней 2-10.
# Каждый следующий уровень дороже предыдущего.
# Настраивается через админку без изменения кода.
DEFAULT_COSTS = [
    # level, metal, wood, blueprints
    (2,   5,   3,  1),
    (3,   8,   5,  2),
    (4,  12,   8,  3),
    (5,  17,  12,  4),
    (6,  23,  17,  6),
    (7,  30,  23,  8),
    (8,  40,  30, 11),
    (9,  52,  40, 15),
    (10, 65,  52, 20),
]


def create_default_costs(apps, schema_editor):
    UpgradeLevelCost = apps.get_model('inventory', 'UpgradeLevelCost')
    rows = []
    for item_type in ('sword', 'shield'):
        for level, metal, wood, blueprints in DEFAULT_COSTS:
            rows.append(UpgradeLevelCost(
                item_type=item_type,
                level=level,
                metal_required=metal,
                wood_required=wood,
                blueprints_required=blueprints,
            ))
    UpgradeLevelCost.objects.bulk_create(rows, ignore_conflicts=True)


def remove_default_costs(apps, schema_editor):
    UpgradeLevelCost = apps.get_model('inventory', 'UpgradeLevelCost')
    levels = [row[0] for row in DEFAULT_COSTS]
    UpgradeLevelCost.objects.filter(level__in=levels).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_upgradelevelcost'),
    ]

    operations = [
        migrations.RunPython(create_default_costs, remove_default_costs),
    ]
