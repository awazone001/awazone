# Generated by Django 5.0.2 on 2024-04-05 05:47

import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Level',
            fields=[
                ('level', models.TextField(choices=[('Level 1', 'Level 1'), ('Level 2', 'Level 2'), ('Level 3', 'Level 3'), ('Level 4', 'Level 4'), ('Level 5', 'Level 5'), ('Level 6', 'Level 6'), ('Level 7', 'Level 7'), ('Level 8', 'Level 8'), ('Level 9', 'Level 9'), ('Level 10', 'Level 10'), ('Level 11', 'Level 11'), ('Level 12', 'Level 12'), ('Level 13', 'Level 13'), ('Level 14', 'Level 14'), ('Level 15', 'Level 15'), ('Level 16', 'Level 16'), ('Level 17', 'Level 17'), ('Level 18', 'Level 18'), ('Level 19', 'Level 19'), ('Level 20', 'Level 20')], primary_key=True, serialize=False, verbose_name='Level')),
                ('title', models.CharField(max_length=100, verbose_name='Rank')),
                ('description', models.TextField(verbose_name='Description')),
                ('direct_team', models.IntegerField(verbose_name='Direct Team Size')),
                ('number_team', models.IntegerField(verbose_name='Total Team Size')),
                ('user_reward', models.TextField(verbose_name='User Reward')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('level',),
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('first_name', models.CharField(max_length=50, verbose_name='First name')),
                ('last_name', models.CharField(max_length=50, verbose_name='Last name')),
                ('username', models.CharField(max_length=50, unique=True, verbose_name='Username')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('profile_image', models.ImageField(default='profile_pictures/avatar.jpg', upload_to='profile_pictures/', verbose_name='Profile Picture')),
                ('phone_number', models.CharField(max_length=11)),
                ('is_active', models.BooleanField(default=False, verbose_name='Account active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff')),
                ('user_code', models.CharField(max_length=200, null=True, unique=True)),
                ('referral_code', models.CharField(blank=True, max_length=200, null=True)),
                ('team', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='AIBO',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_subscribed_for_mail', models.BooleanField(auto_created=True, default=True, verbose_name='Subscribe for Mailing')),
                ('arp', models.FloatField(default=0)),
                ('auto_renew_license', models.BooleanField(default=False, verbose_name='Auto Renew Licenses and Subscription')),
                ('is_valid_for_monthly_license', models.BooleanField(default=True)),
                ('is_valid_for_yearly_license', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_module.level')),
            ],
        ),
        migrations.CreateModel(
            name='Reward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reward', models.TextField()),
                ('title', models.CharField(max_length=100, verbose_name='Description')),
                ('testimonial', models.URLField()),
                ('recieved', models.BooleanField(default=False, verbose_name='recieved')),
                ('qualified', models.BooleanField(default=False, verbose_name='qualified')),
                ('timestamp', models.TimeField(auto_now_add=True)),
                ('datestamp', models.DateField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('user_level', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='user_module.level')),
            ],
            options={
                'ordering': ('user_level',),
            },
        ),
    ]
