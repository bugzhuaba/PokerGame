from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('device', '0003_device_channel_id'),('room', '0005_alter_room_state')]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='table',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='device.device'),
        ),
    ]
