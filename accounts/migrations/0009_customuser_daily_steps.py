# Generated manually for steps quest support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_customuser_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='daily_steps',
            field=models.IntegerField(default=0, help_text='Шаги за сегодня (для квеста steps, обновляется через POST /api/player/daily-steps/)'),
        ),
    ]
