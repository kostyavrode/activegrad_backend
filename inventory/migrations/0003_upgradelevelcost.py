from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_initial_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpgradeLevelCost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(
                    choices=[('sword', 'Меч'), ('shield', 'Щит')],
                    max_length=20,
                    verbose_name='Тип предмета'
                )),
                ('level', models.IntegerField(
                    help_text='Например, 2 = улучшение с 1 до 2',
                    verbose_name='Уровень (до которого улучшаем)'
                )),
                ('metal_required', models.IntegerField(default=0, verbose_name='Металл (требуется)')),
                ('wood_required', models.IntegerField(default=0, verbose_name='Дерево (требуется)')),
                ('blueprints_required', models.IntegerField(default=0, verbose_name='Чертежи (требуется)')),
            ],
            options={
                'verbose_name': 'Стоимость улучшения по уровню',
                'verbose_name_plural': 'Стоимости улучшений по уровням',
                'ordering': ['item_type', 'level'],
                'unique_together': {('item_type', 'level')},
            },
        ),
    ]
