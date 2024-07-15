from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('device', '__init__')]
    operations = [
        migrations.AddField(model_name='device',
        name='status',
        field=models.CharField(choices=[('online', 'Online'), ('offline', 'Offline')], default='online', max_length=10),)]