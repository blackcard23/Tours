# Generated by Django 4.2.16 on 2024-12-14 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0002_remove_transaction_transaction_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='card_name',
            field=models.CharField(max_length=255),
        ),
    ]
