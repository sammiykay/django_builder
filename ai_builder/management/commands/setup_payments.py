from django.core.management.base import BaseCommand
from django.conf import settings
from ai_builder.models import PaymentMethod, BillingPlan


class Command(BaseCommand):
    help = 'Set up payment methods and billing plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all payment methods and plans',
        )

    def handle(self, *args, **options):
        if options['reset']:
            PaymentMethod.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Deleted all existing payment methods')
            )

        # Create Flutterwave payment method
        flutterwave_method, created = PaymentMethod.objects.get_or_create(
            payment_type='flutterwave',
            defaults={
                'name': 'Flutterwave',
                'is_active': True,
                'flutterwave_public_key': getattr(settings, 'FLUTTERWAVE_PUBLIC_KEY', ''),
                'flutterwave_secret_key': getattr(settings, 'FLUTTERWAVE_SECRET_KEY', ''),
                'flutterwave_encryption_key': getattr(settings, 'FLUTTERWAVE_ENCRYPTION_KEY', ''),
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Flutterwave payment method')
            )
        else:
            self.stdout.write('Flutterwave payment method already exists')

        # Create Bitcoin payment method
        bitcoin_method, created = PaymentMethod.objects.get_or_create(
            payment_type='crypto_bitcoin',
            defaults={
                'name': 'Bitcoin',
                'is_active': True,
                'crypto_symbol': 'BTC',
                'crypto_network': 'mainnet',
                'usd_exchange_rate': 45000.00,
                'decimals': 8,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Bitcoin payment method')
            )
        else:
            self.stdout.write('Bitcoin payment method already exists')

        # Create Ethereum payment method
        ethereum_method, created = PaymentMethod.objects.get_or_create(
            payment_type='crypto_ethereum',
            defaults={
                'name': 'Ethereum',
                'is_active': True,
                'crypto_symbol': 'ETH',
                'crypto_network': 'mainnet',
                'usd_exchange_rate': 3000.00,
                'decimals': 18,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Ethereum payment method')
            )
        else:
            self.stdout.write('Ethereum payment method already exists')

        # Create USDT payment method
        usdt_method, created = PaymentMethod.objects.get_or_create(
            payment_type='crypto_usdt',
            defaults={
                'name': 'USDT (Tether)',
                'is_active': True,
                'crypto_symbol': 'USDT',
                'crypto_network': 'mainnet',
                'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT on Ethereum
                'usd_exchange_rate': 1.00,
                'decimals': 6,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created USDT payment method')
            )
        else:
            self.stdout.write('USDT payment method already exists')

        # Create USDC payment method
        usdc_method, created = PaymentMethod.objects.get_or_create(
            payment_type='crypto_usdc',
            defaults={
                'name': 'USDC',
                'is_active': True,
                'crypto_symbol': 'USDC',
                'crypto_network': 'mainnet',
                'contract_address': '0xA0b86a33E6414e5b6f8f10d63bc39A8C4b2aF7a2',  # USDC on Ethereum
                'usd_exchange_rate': 1.00,
                'decimals': 6,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created USDC payment method')
            )
        else:
            self.stdout.write('USDC payment method already exists')

        self.stdout.write(
            self.style.SUCCESS('Payment methods setup completed successfully!')
        )
        
        # Display configuration instructions
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('CONFIGURATION REQUIRED:'))
        self.stdout.write('='*50)
        self.stdout.write('\n1. For Flutterwave integration, add these to your settings:')
        self.stdout.write('   FLUTTERWAVE_PUBLIC_KEY = "your_public_key_here"')
        self.stdout.write('   FLUTTERWAVE_SECRET_KEY = "your_secret_key_here"')
        self.stdout.write('   FLUTTERWAVE_ENCRYPTION_KEY = "your_encryption_key_here"')
        
        self.stdout.write('\n2. For UniPayment crypto payments, add these to your .env file:')
        self.stdout.write('   UNIPAYMENT_CLIENT_ID=your_client_id_here')
        self.stdout.write('   UNIPAYMENT_CLIENT_SECRET=your_client_secret_here')
        self.stdout.write('   UNIPAYMENT_APP_ID=your_app_id_here')
        self.stdout.write('   UNIPAYMENT_SANDBOX=True  # Set to False for production')
        
        self.stdout.write('\n3. Configure callback URLs in your .env file:')
        self.stdout.write('   FRONTEND_URL=http://localhost:3000  # Your frontend URL')
        self.stdout.write('   BACKEND_URL=http://localhost:8000   # Your backend URL')
        
        self.stdout.write('\n4. Set up webhooks:')
        self.stdout.write('   Flutterwave webhook URL: https://yourdomain.com/api/payments/flutterwave/webhook/')
        self.stdout.write('   UniPayment webhook URL: https://yourdomain.com/api/payments/unipayment/webhook/')
        
        self.stdout.write('\n5. Update payment method configurations in Django admin if needed')
        self.stdout.write('   - Configure specific network settings for crypto currencies')
        self.stdout.write('   - Update exchange rates as needed')
        
        self.stdout.write('\n' + '='*50)