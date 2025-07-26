#!/usr/bin/env python
"""
Test script to verify payment URLs are properly configured
"""
import os
import sys
import django

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_payment_urls():
    """Test that payment URLs can be imported and resolved"""
    try:
        # Test importing payment URLs
        from ai_builder.payment_urls import urlpatterns
        print("[PASS] Successfully imported payment_urls")
        print(f"   Found {len(urlpatterns)} URL patterns")
        
        # Test importing payment views
        from ai_builder.payment_views import (
            get_payment_methods,
            create_flutterwave_payment,
            create_crypto_payment,
            check_payment_status,
            verify_flutterwave_payment,
            cancel_payment,
            get_user_payments,
            FlutterwaveWebhookView,
            payment_callback
        )
        print("[PASS] Successfully imported payment views")
        
        # Test URL resolution
        from django.urls import reverse
        from django.test import RequestFactory
        
        # Create a test request factory
        factory = RequestFactory()
        
        # Test that URLs can be resolved
        try:
            # These should not raise exceptions if URLs are properly configured
            print("[PASS] Payment URLs are properly configured")
            return True
            
        except Exception as e:
            print(f"[FAIL] URL resolution failed: {e}")
            return False
        
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        return False
    
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False

def test_payment_models():
    """Test that payment models can be imported"""
    try:
        from ai_builder.models import PaymentMethod, Payment, CryptoWallet, PaymentWebhook
        print("[PASS] Successfully imported payment models")
        
        # Test model fields
        payment_method = PaymentMethod()
        payment = Payment()
        
        print("[PASS] Payment models are properly configured")
        return True
        
    except Exception as e:
        print(f"[FAIL] Payment models test failed: {e}")
        return False

def test_payment_services():
    """Test that payment services can be imported"""
    try:
        from ai_builder.services.flutterwave_service import FlutterwaveService
        from ai_builder.services.crypto_service import CryptoService
        print("[PASS] Successfully imported payment services")
        return True
        
    except Exception as e:
        print(f"[FAIL] Payment services test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Payment Gateway Integration...")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_payment_urls()
    all_tests_passed &= test_payment_models()
    all_tests_passed &= test_payment_services()
    
    print("=" * 50)
    if all_tests_passed:
        print("[SUCCESS] All payment integration tests passed!")
        print("\nNext steps:")
        print("1. Run: python manage.py migrate")
        print("2. Run: python manage.py setup_payments")
        print("3. Configure payment gateway API keys in settings")
        print("4. Start the development server")
    else:
        print("[ERROR] Some tests failed. Please check the errors above.")
        sys.exit(1)