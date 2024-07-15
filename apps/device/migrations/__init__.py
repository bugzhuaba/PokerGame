from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[('device_id', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True)),
                    ('name', models.CharField(blank=True, max_length=100, null=True)),
                    ('type', models.CharField(choices=[('tablet', 'Tablet'), ('mobile', 'Mobile')],
                                              default='mobile',max_length=10))],
            options={'verbose_name': 'Device'},
        ),
    ]