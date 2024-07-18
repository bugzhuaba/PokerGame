import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('device', '0002_device_status'),('room', '0001_initial'),]

    operations = [
        migrations.RemoveField(model_name='room',name='name',),
        migrations.AddField(model_name='room',
                            name='created_at',
                            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
                            preserve_default=False,
                            ),
        migrations.AddField(model_name='room',name='updated_at',field=models.DateTimeField(auto_now=True),),
        migrations.AlterUniqueTogether(name='player', unique_together={('room', 'device'), ('room', 'index')},),]