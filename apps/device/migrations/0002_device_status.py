from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('device', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='device',
            name='status',
            field=models.CharField(choices=[('online', 'Online'), ('offline', 'Offline')], default='online', max_length=10),
        )
    ]