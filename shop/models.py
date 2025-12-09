from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ShopItem(models.Model):
    """
    Модель товара в магазине.
    Управляется через админ панель.
    """
    name = models.CharField(max_length=200, verbose_name="Название товара")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL картинки")
    price = models.IntegerField(verbose_name="Стоимость (coins)")
    promo_code = models.CharField(max_length=100, verbose_name="Промокод", help_text="Промокод, который выдается после покупки")
    is_active = models.BooleanField(default=True, verbose_name="Активен", help_text="Показывать товар в магазине")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.price} coins)"


class UserPromoCode(models.Model):
    """
    Модель для хранения промокодов, купленных пользователем.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_codes', verbose_name="Пользователь")
    shop_item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='purchases', verbose_name="Товар")
    promo_code = models.CharField(max_length=100, verbose_name="Промокод")
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата покупки")
    
    class Meta:
        verbose_name = "Промокод пользователя"
        verbose_name_plural = "Промокоды пользователей"
        ordering = ['-purchased_at']
        unique_together = ('user', 'shop_item', 'promo_code')  # Предотвращает дубликаты
    
    def __str__(self):
        return f"{self.user.username} - {self.promo_code} ({self.shop_item.name})"


class PurchaseHistory(models.Model):
    """
    История покупок пользователя (опционально, для аналитики).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases', verbose_name="Пользователь")
    shop_item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='purchase_history', verbose_name="Товар")
    price_paid = models.IntegerField(verbose_name="Сумма покупки")
    promo_code = models.CharField(max_length=100, verbose_name="Полученный промокод")
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата покупки")
    
    class Meta:
        verbose_name = "История покупки"
        verbose_name_plural = "История покупок"
        ordering = ['-purchased_at']
    
    def __str__(self):
        return f"{self.user.username} купил {self.shop_item.name} за {self.price_paid} coins"

