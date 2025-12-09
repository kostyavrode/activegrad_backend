# Generated manually for shop app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название товара')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('image_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='URL картинки')),
                ('price', models.IntegerField(verbose_name='Стоимость (coins)')),
                ('promo_code', models.CharField(help_text='Промокод, который выдается после покупки', max_length=100, verbose_name='Промокод')),
                ('is_active', models.BooleanField(default=True, help_text='Показывать товар в магазине', verbose_name='Активен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserPromoCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('promo_code', models.CharField(max_length=100, verbose_name='Промокод')),
                ('purchased_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата покупки')),
                ('shop_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='shop.shopitem', verbose_name='Товар')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='promo_codes', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Промокод пользователя',
                'verbose_name_plural': 'Промокоды пользователей',
                'ordering': ['-purchased_at'],
                'unique_together': {('user', 'shop_item', 'promo_code')},
            },
        ),
        migrations.CreateModel(
            name='PurchaseHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_paid', models.IntegerField(verbose_name='Сумма покупки')),
                ('promo_code', models.CharField(max_length=100, verbose_name='Полученный промокод')),
                ('purchased_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата покупки')),
                ('shop_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchase_history', to='shop.shopitem', verbose_name='Товар')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'История покупки',
                'verbose_name_plural': 'История покупок',
                'ordering': ['-purchased_at'],
            },
        ),
    ]

