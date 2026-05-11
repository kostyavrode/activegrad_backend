from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class PlayerLandmarkObservation(models.Model):
    """
    Модель для хранения факта наблюдения игрока в достопримечательности.
    Хранит только external_id (ID из Wikipedia API), название и описание
    получаются из Unity приложения через Wikipedia API.
    """
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='landmark_observations')
    external_id = models.CharField(max_length=200, help_text="ID достопримечательности из Wikipedia API")
    observed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('player', 'external_id')
        ordering = ['-observed_at']
        indexes = [
            models.Index(fields=['player', 'external_id']),
        ]
    
    def __str__(self):
        return f"{self.player.username} at landmark {self.external_id}"


class LandmarkCapture(models.Model):
    """
    Модель для хранения захвата достопримечательности игроком.
    Хранит информацию о том, кто захватил достопримечательность, когда и какой клан.
    """
    external_id = models.CharField(
        max_length=200, 
        help_text="ID достопримечательности из Wikipedia API",
        db_index=True
    )
    captured_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='landmark_captures',
        verbose_name="Игрок, который захватил"
    )
    clan = models.ForeignKey(
        'clans.Clan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='landmark_captures',
        verbose_name="Клан"
    )
    captured_at = models.DateTimeField(auto_now_add=True, verbose_name="Время захвата")
    
    class Meta:
        verbose_name = "Захват достопримечательности"
        verbose_name_plural = "Захваты достопримечательностей"
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['external_id', '-captured_at']),
            models.Index(fields=['clan']),
        ]
    
    def __str__(self):
        clan_name = self.clan.name if self.clan else "без клана"
        return f"{self.captured_by.username} ({clan_name}) захватил {self.external_id}"
    
    @staticmethod
    def get_latest_capture(external_id):
        """Получает последний захват достопримечательности."""
        try:
            return LandmarkCapture.objects.filter(external_id=external_id).latest('captured_at')
        except LandmarkCapture.DoesNotExist:
            return None
    
    # Время неприступности после захвата (никто не может перехватить)
    INVULNERABILITY_MINUTES = 30

    FAILED_CAPTURE_COOLDOWN_MINUTES = 5  # Кулдаун после неудачной попытки

    @staticmethod
    def can_capture(external_id):
        """
        Проверяет, можно ли захватить достопримечательность.
        Возвращает (можно_ли_захватить, последний_захват или None, fail_cooldown или None).
        Блокировки: 30 мин после захвата, 5 мин после неудачной попытки.
        """
        latest_capture = LandmarkCapture.get_latest_capture(external_id)
        now = timezone.now()

        # Если достопримечательность еще никто не захватывал
        if latest_capture is None:
            # Проверяем кулдаун после неудачи (если кто-то пытался захватить пустую и провалился — маловероятно, но на всякий случай)
            fail_cooldown = LandmarkCaptureCooldown.objects.filter(
                external_id=external_id, cooldown_until__gt=now
            ).first()
            if fail_cooldown:
                return False, None, fail_cooldown
            return True, None, None

        # Проверяем, прошло ли 30 минут с последнего захвата
        time_since_capture = now - latest_capture.captured_at
        invulnerability = timedelta(minutes=LandmarkCapture.INVULNERABILITY_MINUTES)
        if time_since_capture < invulnerability:
            return False, latest_capture, None

        # Проверяем кулдаун 5 минут после неудачной попытки
        fail_cooldown = LandmarkCaptureCooldown.objects.filter(
            external_id=external_id, cooldown_until__gt=now
        ).first()
        if fail_cooldown:
            return False, latest_capture, fail_cooldown

        return True, latest_capture, None
    
    def time_until_next_capture_allowed(self):
        """Возвращает время, через которое можно будет попытаться перехватить (timedelta)."""
        time_since_capture = timezone.now() - self.captured_at
        time_required = timedelta(minutes=LandmarkCapture.INVULNERABILITY_MINUTES)
        remaining = time_required - time_since_capture
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


class LandmarkCaptureCooldown(models.Model):
    """
    Кулдаун 5 минут после неудачной попытки захвата.
    В течение этого времени повторный захват невозможен.
    """
    external_id = models.CharField(max_length=200, db_index=True, unique=True)
    cooldown_until = models.DateTimeField(verbose_name="До какого времени нельзя захватывать")

    class Meta:
        verbose_name = "Кулдаун захвата (после неудачи)"
        verbose_name_plural = "Кулдауны захватов"

    def time_remaining(self):
        """Время до окончания кулдауна."""
        remaining = self.cooldown_until - timezone.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)


class LandmarkCaptureRewardCollection(models.Model):
    """
    Отслеживает, сколько часовых наград уже собрано за конкретный захват.
    При смене владельца создаётся новый LandmarkCapture — и новая запись.
    Максимум 8 часов наград на захват.
    """
    MAX_REWARD_HOURS = 8

    capture = models.OneToOneField(
        LandmarkCapture,
        on_delete=models.CASCADE,
        related_name='reward_collection',
    )
    hours_collected = models.IntegerField(default=0, verbose_name="Часов уже собрано")

    class Meta:
        verbose_name = "Сбор ресурсов за захват"
        verbose_name_plural = "Сборы ресурсов за захваты"

    def available_hours(self):
        """Количество новых целых часов, доступных для сбора.
        После 8 часов с момента захвата точка перестаёт приносить ресурсы."""
        elapsed_seconds = (timezone.now() - self.capture.captured_at).total_seconds()
        if elapsed_seconds >= self.MAX_REWARD_HOURS * 3600:
            return 0
        whole_hours = int(elapsed_seconds // 3600)
        return max(0, whole_hours - self.hours_collected)
