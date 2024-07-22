from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('room', '0003_player_channel_id_room_state')]
    operations = [
        migrations.AddField(
            model_name='player',
            name='status',
            field=models.CharField(
                choices=[('online', 'Online'), ('offline', 'Offline'), ('exit', 'Exit'), ('lose', 'Lose')],
                default='offline', max_length=10),
        )
        ]