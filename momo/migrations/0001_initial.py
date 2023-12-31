# Generated by Django 3.2.23 on 2023-12-19 06:49

from django.db import migrations, models
import django.utils.timezone
import utils.uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modified_on', models.DateTimeField(auto_now=True, db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('access_token', models.TextField()),
                ('token_type', models.CharField(choices=[('access_token', 'access_token'), ('0auth2', '0auth2')], default='access_token', max_length=30)),
                ('expires_in', models.IntegerField(default=3600)),
                ('expired', models.BooleanField(default=False)),
                ('scope', models.CharField(max_length=100, null=True)),
                ('refresh_token', models.CharField(max_length=50, null=True)),
                ('refresh_token_expired_in', models.IntegerField(default=0)),
                ('created_on', models.DateTimeField(blank=True, default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'db_table': 'momo_access_token',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='APIUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified_on', models.DateTimeField(auto_now=True, db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('x_reference_id', models.UUIDField(default=utils.uuid.generate_uuid, help_text='User x-reference Id', unique=True)),
                ('target_environment', models.CharField(choices=[('sandbox', 'sandbox'), ('production', 'production')], help_text='Environment in which the user operates', max_length=15)),
                ('callback_host', models.URLField(help_text='We shall send this in a header as call back when creating the API user')),
                ('ocp_apim_subscription_key', models.CharField(max_length=33, null=True)),
                ('api_key', models.CharField(help_text='This will be used to generate an Access token', max_length=33, null=True)),
            ],
            options={
                'db_table': 'momo_api_user',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Product name', max_length=200)),
                ('product_type', models.CharField(choices=[('collection', 'Collection'), ('disbursement', 'Disbursement'), ('remittance', 'Remittance')], help_text='Represents MTN MOMO API product', max_length=20)),
                ('primary_key', models.CharField(help_text='MOMO Product subscription primary key', max_length=33)),
                ('secondary_key', models.CharField(help_text='MOMO Product subscription secondary key', max_length=33)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
