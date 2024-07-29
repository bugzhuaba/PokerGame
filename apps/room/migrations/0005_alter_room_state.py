from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('room','0004_player_status')]
    operations = [
        migrations.AlterField(
            model_name='room',
            name='state',
            field=models.JSONField(default={}),
        ),
    ]