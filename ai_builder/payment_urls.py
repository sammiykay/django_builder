from django.urls import path
from .payment_views import (
    get_payment_methods,
    create_flutterwave_payment,
    create_crypto_payment,
    create_crypto_invoice,
    notify_url_handler,
    check_payment_status,
    verify_flutterwave_payment,
    cancel_payment,
    get_user_payments,
    test_webhook_config,
    FlutterwaveWebhookView,
    NOWPaymentsWebhookView,
    payment_callback
)

urlpatterns = [
    # Payment methods
    path('methods/', get_payment_methods, name='get_payment_methods'),
    
    # Flutterwave payments
    path('flutterwave/create/', create_flutterwave_payment, name='create_flutterwave_payment'),
    path('flutterwave/verify/', verify_flutterwave_payment, name='verify_flutterwave_payment'),
    path('flutterwave/webhook/', FlutterwaveWebhookView.as_view(), name='flutterwave_webhook'),
    
    # NOWPayments webhooks (consolidated to avoid confusion)
    path('nowpayments/webhook/', NOWPaymentsWebhookView.as_view(), name='nowpayments_webhook'),
    # Legacy handler - redirects to main webhook for backwards compatibility
    path('handler/', notify_url_handler, name='notify_url_handler'),
    
    # Crypto payments
    path('crypto/create/', create_crypto_payment, name='create_crypto_payment'),
    path('crypto/invoice/', create_crypto_invoice, name='create_crypto_invoice'),
    
    # Payment history and callbacks (specific paths first)
    path('test-webhook/', test_webhook_config, name='test_webhook_config'),
    path('history/', get_user_payments, name='get_user_payments'),
    path('callback/', payment_callback, name='payment_callback'),
    
    # Payment management with dynamic reference (MUST BE LAST)
    path('status/<str:reference>/', check_payment_status, name='check_payment_status'),
    path('cancel/<str:reference>/', cancel_payment, name='cancel_payment'),
]