# Generated by Django 4.2.6 on 2025-03-20 05:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_farmer_aadhar_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyFarmerCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('count', models.IntegerField(default=0)),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.block')),
                ('surveyor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('surveyor', 'date')},
            },
        ),
    ]
