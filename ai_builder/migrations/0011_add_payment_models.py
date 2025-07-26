# Generated migration for payment models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ai_builder', '0010_remove_billingplan_advanced_features_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('payment_type', models.CharField(choices=[('flutterwave', 'Flutterwave'), ('crypto_bitcoin', 'Bitcoin'), ('crypto_ethereum', 'Ethereum'), ('crypto_usdt', 'USDT (Tether)'), ('crypto_usdc', 'USDC')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('flutterwave_public_key', models.CharField(blank=True, max_length=200)),
                ('flutterwave_secret_key', models.CharField(blank=True, max_length=200)),
                ('flutterwave_encryption_key', models.CharField(blank=True, max_length=200)),
                ('crypto_symbol', models.CharField(blank=True, help_text='BTC, ETH, USDT, etc.', max_length=10)),
                ('crypto_network', models.CharField(blank=True, choices=[('mainnet', 'Mainnet'), ('testnet', 'Testnet'), ('polygon', 'Polygon'), ('bsc', 'BSC'), ('arbitrum', 'Arbitrum')], max_length=20)),
                ('wallet_address', models.CharField(blank=True, max_length=200)),
                ('contract_address', models.CharField(blank=True, help_text='For tokens like USDT', max_length=200)),
                ('decimals', models.IntegerField(default=18, help_text='Token decimals')),
                ('usd_exchange_rate', models.DecimalField(decimal_places=8, default=1.0, max_digits=20)),
                ('last_rate_update', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_id', models.CharField(max_length=100, unique=True)),
                ('reference', models.CharField(help_text='Internal reference', max_length=100, unique=True)),
                ('purpose', models.CharField(choices=[('subscription', 'Subscription Payment'), ('upgrade', 'Plan Upgrade'), ('token_purchase', 'Token Purchase'), ('overage', 'Token Overage')], max_length=20)),
                ('amount_usd', models.DecimalField(decimal_places=2, max_digits=10)),
                ('amount_paid', models.DecimalField(decimal_places=8, help_text='Amount in payment currency', max_digits=20)),
                ('currency', models.CharField(help_text='USD, BTC, ETH, etc.', max_length=10)),
                ('exchange_rate', models.DecimalField(decimal_places=8, default=1.0, max_digits=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('gateway_transaction_id', models.CharField(blank=True, max_length=200)),
                ('gateway_response', models.JSONField(blank=True, default=dict)),
                ('crypto_address', models.CharField(blank=True, help_text='Payment address', max_length=200)),
                ('transaction_hash', models.CharField(blank=True, max_length=200)),
                ('block_confirmations', models.IntegerField(default=0)),
                ('required_confirmations', models.IntegerField(default=3)),
                ('webhook_received', models.BooleanField(default=False)),
                ('webhook_data', models.JSONField(blank=True, default=dict)),
                ('callback_url', models.URLField(blank=True)),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ai_builder.billinginvoice')),
                ('payment_method', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ai_builder.paymentmethod')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ai_builder.usersubscription')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CryptoWallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=200, unique=True)),
                ('private_key_encrypted', models.TextField(help_text='Encrypted private key')),
                ('is_active', models.BooleanField(default=True)),
                ('balance', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('last_balance_check', models.DateTimeField(blank=True, null=True)),
                ('total_received', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('payment_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payment_method', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallets', to='ai_builder.paymentmethod')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentWebhook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('webhook_type', models.CharField(choices=[('flutterwave', 'Flutterwave'), ('crypto_confirmation', 'Crypto Confirmation'), ('manual', 'Manual Update')], max_length=20)),
                ('webhook_id', models.CharField(blank=True, max_length=200)),
                ('event_type', models.CharField(max_length=100)),
                ('raw_data', models.JSONField(default=dict)),
                ('processed', models.BooleanField(default=False)),
                ('success', models.BooleanField(default=False)),
                ('error_message', models.TextField(blank=True)),
                ('actions_taken', models.JSONField(default=list, help_text='List of actions performed')),
                ('signature_valid', models.BooleanField(default=False)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('payment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='webhooks', to='ai_builder.payment')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', '-created_at'], name='ai_builder_payment_user_id_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status', '-created_at'], name='ai_builder_payment_status_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['payment_method', '-created_at'], name='ai_builder_payment_payment_method_id_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['reference'], name='ai_builder_payment_reference_idx'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['transaction_hash'], name='ai_builder_payment_transaction_hash_idx'),
        ),
    ]