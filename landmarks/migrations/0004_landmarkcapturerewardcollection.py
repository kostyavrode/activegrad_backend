from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('landmarks', '0003_landmarkcapturecooldown'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandmarkCaptureRewardCollection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('capture', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reward_collection',
                    to='landmarks.landmarkcapture',
                )),
                ('hours_collected', models.IntegerField(default=0, verbose_name='Часов уже собрано')),
            ],
            options={
                'verbose_name': 'Сбор ресурсов за захват',
                'verbose_name_plural': 'Сборы ресурсов за захваты',
            },
        ),
    ]
