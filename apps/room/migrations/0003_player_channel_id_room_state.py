from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [ ('room', '0002_remove_room_name_room_created_at_room_updated_at_and_more')]

    operations = [
        migrations.AddField(
            model_name='player',
            name='channel_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='room',
            name='state',
            field=models.JSONField(default='{}'),
            preserve_default=False)
    ]