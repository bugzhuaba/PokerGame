import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('device', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('player_count', models.IntegerField()),
                ('status',models.CharField(choices=[('waiting', 'Waiting'), ('playing', 'Playing'), ('finished', 'Finished')],default='waiting', max_length=10)),
                ('table', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,to='device.device')),
            ],
            options={'verbose_nsme':'Room'},),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField(default=1)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='device.device')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='room.room')),
            ],
            options={'verbose_name': 'RoomPlayer'},),]


