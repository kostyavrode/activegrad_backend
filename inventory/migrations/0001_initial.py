# Generated manually for inventory app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CraftRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(choices=[('sword', 'Меч'), ('shield', 'Щит')], max_length=20, unique=True, verbose_name='Тип предмета')),
                ('metal_required', models.IntegerField(default=1, verbose_name='Металл (требуется)')),
                ('wood_required', models.IntegerField(default=1, verbose_name='Дерево (требуется)')),
                ('blueprints_required', models.IntegerField(default=1, verbose_name='Чертежи (требуется)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Рецепт крафта',
                'verbose_name_plural': 'Рецепты крафта',
            },
        ),
        migrations.CreateModel(
            name='UpgradeConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(choices=[('sword', 'Меч'), ('shield', 'Щит')], max_length=20, unique=True, verbose_name='Тип предмета')),
                ('base_probability', models.FloatField(default=0.0, help_text='Минимальная вероятность успеха без ресурсов', verbose_name='Базовая вероятность (0-100)')),
                ('metal_prob_per_unit', models.FloatField(default=5.0, verbose_name='Вероятность за 1 металл (%)')),
                ('wood_prob_per_unit', models.FloatField(default=5.0, verbose_name='Вероятность за 1 дерево (%)')),
                ('blueprints_prob_per_unit', models.FloatField(default=5.0, verbose_name='Вероятность за 1 чертёж (%)')),
                ('max_probability', models.FloatField(default=95.0, help_text='Вероятность не превысит это значение', verbose_name='Макс. вероятность (%)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Настройка улучшения',
                'verbose_name_plural': 'Настройки улучшения',
            },
        ),
        migrations.CreateModel(
            name='PlayerInventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metal', models.IntegerField(default=0, verbose_name='Металл')),
                ('wood', models.IntegerField(default=0, verbose_name='Дерево')),
                ('blueprints', models.IntegerField(default=0, verbose_name='Чертежи')),
                ('sword_sharpness', models.IntegerField(blank=True, default=None, help_text='Уровень остроты меча. null = меча нет.', null=True, verbose_name='Острота меча')),
                ('shield_durability', models.IntegerField(blank=True, default=None, help_text='Уровень стойкости щита. null = щита нет.', null=True, verbose_name='Стойкость щита')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to=settings.AUTH_USER_MODEL, verbose_name='Игрок')),
            ],
            options={
                'verbose_name': 'Инвентарь игрока',
                'verbose_name_plural': 'Инвентари игроков',
            },
        ),
    ]
