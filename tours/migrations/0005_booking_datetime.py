# Generated by Django 4.2.16 on 2024-12-14 18:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0004_alter_booking_booking_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
