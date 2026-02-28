# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landmarks', '0002_auto_20251203_2217'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandmarkCaptureCooldown',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(db_index=True, max_length=200, unique=True)),
                ('cooldown_until', models.DateTimeField(verbose_name='До какого времени нельзя захватывать')),
            ],
            options={
                'verbose_name': 'Кулдаун захвата (после неудачи)',
                'verbose_name_plural': 'Кулдауны захватов',
            },
        ),
    ]
