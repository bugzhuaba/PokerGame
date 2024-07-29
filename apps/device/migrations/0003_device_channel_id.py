from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0002_device_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='channel_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='channel id'),
        ),
    ]



