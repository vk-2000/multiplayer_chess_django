# Generated by Django 3.2.6 on 2022-01-11 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multiplayer_chess', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='friends',
            field=models.ManyToManyField(blank=True, related_name='Friends', to='multiplayer_chess.Player'),
        ),
    ]
