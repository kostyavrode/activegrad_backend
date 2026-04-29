import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quests', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Добавляем поле type к Quest
        migrations.AddField(
            model_name='quest',
            name='type',
            field=models.CharField(
                choices=[
                    ('mark_sights', 'Mark Sights'),
                    ('visit_sights', 'Visit Sights'),
                    ('steps', 'Steps'),
                    ('collect_coins', 'Collect Coins'),
                    ('level_up', 'Level Up'),
                ],
                default='steps',
                help_text='Тип условия квеста. КРИТИЧЕСКИ ВАЖНО - не может быть пустым!',
                max_length=50,
            ),
            preserve_default=False,
        ),
        # Расширяем title
        migrations.AlterField(
            model_name='quest',
            name='title',
            field=models.CharField(help_text='Название квеста', max_length=200),
        ),
        # Расширяем description
        migrations.AlterField(
            model_name='quest',
            name='description',
            field=models.TextField(help_text='Описание квеста', max_length=500),
        ),
        # Добавляем reward_type
        migrations.AddField(
            model_name='quest',
            name='reward_type',
            field=models.CharField(
                choices=[('coins', 'Coins'), ('experience', 'Experience'), ('item', 'Item')],
                default='coins',
                help_text="Тип награды: coins, experience, item",
                max_length=50,
            ),
        ),
        # Добавляем reward_amount
        migrations.AddField(
            model_name='quest',
            name='reward_amount',
            field=models.IntegerField(default=0, help_text='Количество награды (>= 0)'),
        ),
        # Добавляем item_id
        migrations.AddField(
            model_name='quest',
            name='item_id',
            field=models.IntegerField(blank=True, help_text="ID предмета (требуется если reward_type='item')", null=True),
        ),
        # Добавляем promo_code
        migrations.AddField(
            model_name='quest',
            name='promo_code',
            field=models.CharField(
                blank=True,
                help_text='Промокод, который выдается за выполнение квеста',
                max_length=100,
                null=True,
            ),
        ),
        # Добавляем image_url
        migrations.AddField(
            model_name='quest',
            name='image_url',
            field=models.URLField(blank=True, help_text='URL картинки квеста', max_length=500, null=True),
        ),
        # Добавляем is_active
        migrations.AddField(
            model_name='quest',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Активен ли квест'),
        ),
        # Добавляем created_at (с дефолтом для существующих строк)
        migrations.AddField(
            model_name='quest',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Добавляем updated_at
        migrations.AddField(
            model_name='quest',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Добавляем ordering к Quest
        migrations.AlterModelOptions(
            name='quest',
            options={'ordering': ['-created_at'], 'verbose_name': 'Квест', 'verbose_name_plural': 'Квесты'},
        ),
        # Добавляем ordering к DailyQuest
        migrations.AlterModelOptions(
            name='dailyquest',
            options={'ordering': ['-date'], 'verbose_name': 'Ежедневный квест', 'verbose_name_plural': 'Ежедневные квесты'},
        ),
        # Создаём модель QuestProgress
        migrations.CreateModel(
            name='QuestProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_progress', models.IntegerField(default=0, help_text='Текущий прогресс выполнения')),
                ('is_completed', models.BooleanField(default=False, help_text='Выполнен ли квест')),
                ('reward_claimed', models.BooleanField(default=False, help_text='Получена ли награда')),
                ('date', models.DateField(help_text='Дата квеста')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('daily_quest', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='progresses',
                    to='quests.dailyquest',
                )),
                ('quest', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='progresses',
                    to='quests.quest',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='quest_progresses',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Прогресс квеста',
                'verbose_name_plural': 'Прогрессы квестов',
                'ordering': ['-date', '-created_at'],
                'unique_together': {('user', 'quest', 'date')},
            },
        ),
    ]
