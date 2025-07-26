import requests
import hmac
import hashlib
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, Optional, Tuple

from ..models import Payment, PaymentMethod, UserSubscription, BillingPlan


class FlutterwaveService:
    """
    Service for handling Flutterwave payment integration
    """
    
    def __init__(self, payment_method: PaymentMethod = None):
        if payment_method and payment_method.is_flutterwave:
            self.payment_method = payment_method
            self.public_key = payment_method.flutterwave_public_key
            self.secret_key = payment_method.flutterwave_secret_key
            self.encryption_key = payment_method.flutterwave_encryption_key
        else:
            # Try to get default Flutterwave payment method
            self.payment_method = PaymentMethod.objects.filter(
                payment_type='flutterwave', is_active=True
            ).first()
            
            if self.payment_method:
                self.public_key = self.payment_method.flutterwave_public_key
                self.secret_key = self.payment_method.flutterwave_secret_key
                self.encryption_key = self.payment_method.flutterwave_encryption_key
            else:
                raise ValueError("No active Flutterwave payment method found")
        
        self.base_url = "https://api.flutterwave.com/v3"
        
    def create_payment_link(self, user, plan: BillingPlan, 
                          purpose: str = 'subscription') -> Tuple[bool, Dict[str, Any]]:
        """
        Create a payment link for subscription or upgrade
        """
        try:
            # Create payment record
            payment = Payment.objects.create(
                user=user,
                payment_method=self.payment_method,
                purpose=purpose,
                amount_usd=plan.price,
                amount_paid=plan.price,
                currency='USD',
                exchange_rate=Decimal('1.0'),
                expires_at=timezone.now() + timedelta(hours=1),  # 1 hour expiry
                payment_id=f"FLW_{uuid.uuid4().hex[:12].upper()}"
            )
            
            # Prepare payment data
            payload = {
                "tx_ref": payment.reference,
                "amount": str(plan.price),
                "currency": "USD",
                "redirect_url": self._get_callback_url(),
                "payment_options": "card,banktransfer,ussd,mobilemoney",
                "customer": {
                    "email": user.email,
                    "phone_number": getattr(user.profile, 'phone_number', '') if hasattr(user, 'profile') else '',
                    "name": f"{user.first_name} {user.last_name}".strip() or user.username
                },
                "customizations": {
                    "title": f"Payment for {plan.name}",
                    "description": f"Subscription to {plan.name} plan",
                    "logo": self._get_logo_url()
                },
                "meta": {
                    "user_id": user.id,
                    "plan_id": plan.id,
                    "purpose": purpose,
                    "payment_reference": payment.reference
                }
            }
            
            # Make API request
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    payment_link = data['data']['link']
                    
                    # Update payment with gateway info
                    payment.gateway_transaction_id = data['data']['id']
                    payment.gateway_response = data
                    payment.callback_url = payment_link
                    payment.save()
                    
                    return True, {
                        'payment_link': payment_link,
                        'payment_reference': payment.reference,
                        'amount': str(plan.price),
                        'currency': 'USD',
                        'expires_at': payment.expires_at.isoformat()
                    }
            
            # Handle error response
            error_data = response.json() if response.content else {}
            return False, {
                'error': 'Failed to create payment link',
                'details': error_data.get('message', 'Unknown error'),
                'status_code': response.status_code
            }
            
        except Exception as e:
            return False, {
                'error': 'Payment service error',
                'details': str(e)
            }
    
    def verify_payment(self, transaction_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify a payment transaction with Flutterwave
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.secret_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/transactions/{transaction_id}/verify",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    transaction_data = data['data']
                    
                    # Find payment by reference
                    tx_ref = transaction_data.get('tx_ref')
                    if tx_ref:
                        try:
                            payment = Payment.objects.get(reference=tx_ref)
                            
                            # Update payment status
                            if transaction_data.get('status') == 'successful':
                                payment.status = 'completed'
                                payment.completed_at = timezone.now()
                                payment.gateway_response = data
                                payment.save()
                                
                                # Process successful payment
                                self._process_successful_payment(payment)
                                
                                return True, {
                                    'payment_verified': True,
                                    'status': 'completed',
                                    'amount': transaction_data.get('amount'),
                                    'currency': transaction_data.get('currency'),
                                    'reference': tx_ref
                                }
                            else:
                                payment.status = 'failed'
                                payment.gateway_response = data
                                payment.save()
                                
                                return False, {
                                    'payment_verified': False,
                                    'status': 'failed',
                                    'message': transaction_data.get('processor_response', 'Payment failed')
                                }
                                
                        except Payment.DoesNotExist:
                            return False, {
                                'error': 'Payment record not found',
                                'reference': tx_ref
                            }
            
            return False, {
                'error': 'Verification failed',
                'status_code': response.status_code,
                'details': response.json() if response.content else {}
            }
            
        except Exception as e:
            return False, {
                'error': 'Verification service error',
                'details': str(e)
            }
    
    def process_webhook(self, webhook_data: Dict[str, Any], 
                       signature: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process Flutterwave webhook notifications
        """
        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(webhook_data, signature):
                return False, {'error': 'Invalid webhook signature'}
            
            event_type = webhook_data.get('event')
            if event_type != 'charge.completed':
                return True, {'message': 'Event ignored', 'event_type': event_type}
            
            # Extract transaction data
            transaction_data = webhook_data.get('data', {})
            tx_ref = transaction_data.get('tx_ref')
            
            if not tx_ref:
                return False, {'error': 'No transaction reference found'}
            
            try:
                payment = Payment.objects.get(reference=tx_ref)
                
                if transaction_data.get('status') == 'successful':
                    if payment.status != 'completed':
                        payment.status = 'completed'
                        payment.completed_at = timezone.now()
                        payment.webhook_received = True
                        payment.webhook_data = webhook_data
                        payment.save()
                        
                        # Process successful payment
                        self._process_successful_payment(payment)
                    
                    return True, {
                        'payment_processed': True,
                        'reference': tx_ref,
                        'status': 'completed'
                    }
                else:
                    payment.status = 'failed'
                    payment.webhook_received = True
                    payment.webhook_data = webhook_data
                    payment.save()
                    
                    return True, {
                        'payment_processed': True,
                        'reference': tx_ref,
                        'status': 'failed'
                    }
                    
            except Payment.DoesNotExist:
                return False, {
                    'error': 'Payment record not found',
                    'reference': tx_ref
                }
                
        except Exception as e:
            return False, {
                'error': 'Webhook processing error',
                'details': str(e)
            }
    
    def _process_successful_payment(self, payment: Payment):
        """
        Process successful payment - update subscription, generate invoice, etc.
        """
        try:
            # Mark payment as completed (if not already done)
            if payment.status != 'completed':
                payment.mark_completed()
            
            # Handle subscription payments
            if payment.purpose in ['subscription', 'upgrade']:
                # Get the plan from payment metadata or find user's subscription
                try:
                    subscription = UserSubscription.objects.get(user=payment.user)
                    if payment.purpose == 'upgrade':
                        # Find new plan from payment metadata
                        gateway_response = payment.gateway_response or {}
                        meta = gateway_response.get('data', {}).get('meta', {})
                        plan_id = meta.get('plan_id')
                        
                        if plan_id:
                            new_plan = BillingPlan.objects.get(id=plan_id)
                            subscription.plan = new_plan
                            subscription.save()
                    
                    # Update subscription status
                    subscription.status = 'active'
                    subscription.last_payment_date = payment.completed_at
                    
                    # Calculate next payment date
                    if subscription.plan.billing_interval == 'monthly':
                        subscription.next_payment_date = payment.completed_at + timedelta(days=30)
                    elif subscription.plan.billing_interval == 'yearly':
                        subscription.next_payment_date = payment.completed_at + timedelta(days=365)
                    
                    subscription.save()
                    
                except UserSubscription.DoesNotExist:
                    # Create new subscription if doesn't exist
                    gateway_response = payment.gateway_response or {}
                    meta = gateway_response.get('data', {}).get('meta', {})
                    plan_id = meta.get('plan_id')
                    
                    if plan_id:
                        from ..billing_services import BillingService
                        plan = BillingPlan.objects.get(id=plan_id)
                        billing_service = BillingService()
                        billing_service.create_subscription(payment.user, plan)
            
        except Exception as e:
            # Log error but don't fail the payment processing
            print(f"Error processing successful payment {payment.reference}: {str(e)}")
    
    def _verify_webhook_signature(self, webhook_data: Dict[str, Any], 
                                 signature: str) -> bool:
        """
        Verify Flutterwave webhook signature
        """
        try:
            # Flutterwave uses secret key for verification
            payload = str(webhook_data).encode('utf-8')
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False
    
    def _get_callback_url(self) -> str:
        """
        Get the callback URL for payment redirects
        """
        from django.urls import reverse
        from django.contrib.sites.models import Site
        
        try:
            current_site = Site.objects.get_current()
            callback_path = reverse('payment_callback')
            return f"https://{current_site.domain}{callback_path}"
        except:
            # Fallback URL
            return getattr(settings, 'PAYMENT_CALLBACK_URL', 'http://localhost:3000/billing/callback')
    
    def _get_logo_url(self) -> str:
        """
        Get the logo URL for payment customization
        """
        return getattr(settings, 'PAYMENT_LOGO_URL', '')
    
    def get_payment_status(self, reference: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get payment status by reference
        """
        try:
            payment = Payment.objects.get(reference=reference)
            
            return True, {
                'reference': payment.reference,
                'status': payment.status,
                'amount_usd': str(payment.amount_usd),
                'currency': payment.currency,
                'created_at': payment.created_at.isoformat(),
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                'expires_at': payment.expires_at.isoformat() if payment.expires_at else None,
                'is_expired': payment.expires_at and timezone.now() > payment.expires_at,
                'gateway_transaction_id': payment.gateway_transaction_id
            }
            
        except Payment.DoesNotExist:
            return False, {'error': 'Payment not found'}
    
    def cancel_payment(self, reference: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Cancel a pending payment
        """
        try:
            payment = Payment.objects.get(reference=reference, status='pending')
            payment.status = 'cancelled'
            payment.save()
            
            return True, {
                'reference': reference,
                'status': 'cancelled',
                'message': 'Payment cancelled successfully'
            }
            
        except Payment.DoesNotExist:
            return False, {'error': 'Payment not found or cannot be cancelled'}