# Generated by Django 5.0.2 on 2024-04-20 06:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_module', '0006_alter_level_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aibo',
            name='is_subscribed_for_mail',
        ),
    ]