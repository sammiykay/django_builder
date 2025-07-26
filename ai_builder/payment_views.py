from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
import json
import logging

from .models import BillingPlan, PaymentMethod, Payment, UserSubscription
from .services.flutterwave_service import FlutterwaveService
from .services.nowpayments_service import NOWPaymentsService
from .serializers import BillingPlanSerializer, PaymentMethodSerializer
import uuid
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

def get_webhook_url(request):
    """
    Generate consistent webhook URL using BACKEND_URL setting or request context
    """
    backend_url = getattr(settings, 'BACKEND_URL', None)
    
    if backend_url:
        # Use configured BACKEND_URL (recommended for production)
        webhook_path = reverse('ai_builder:nowpayments_webhook')
        webhook_url = f"{backend_url.rstrip('/')}{webhook_path}"
        logger.info(f"Using configured BACKEND_URL for webhook: {webhook_url}")
    else:
        # Fallback to request-based URL (development only)
        webhook_url = request.build_absolute_uri('/api/payments/nowpayments/webhook/')
        logger.warning(f"BACKEND_URL not configured, using request-based URL: {webhook_url}")
    
    return webhook_url


@api_view(['GET'])
@permission_classes([])  # Temporarily remove auth for testing
def get_payment_methods(request):
    """
    Get available payment methods
    """
    try:
        payment_methods = PaymentMethod.objects.filter(is_active=True)
        serializer = PaymentMethodSerializer(payment_methods, many=True)
        
        return Response({
            'success': True,
            'payment_methods': serializer.data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Failed to get payment methods',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_flutterwave_payment(request):
    """
    Create a Flutterwave payment link
    """
    try:
        plan_id = request.data.get('plan_id')
        purpose = request.data.get('purpose', 'subscription')
        
        if not plan_id:
            return Response({
                'success': False,
                'error': 'Plan ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        plan = get_object_or_404(BillingPlan, id=plan_id)
        
        # Get Flutterwave payment method
        payment_method = PaymentMethod.objects.filter(
            payment_type='flutterwave',
            is_active=True
        ).first()
        
        if not payment_method:
            return Response({
                'success': False,
                'error': 'Flutterwave payment method not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create payment link
        flutterwave_service = FlutterwaveService(payment_method)
        success, result = flutterwave_service.create_payment_link(
            request.user, plan, purpose
        )
        
        if success:
            return Response({
                'success': True,
                'data': result
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to create payment link'),
                'details': result.get('details')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error creating Flutterwave payment: {str(e)}")
        return Response({
            'success': False,
            'error': 'Payment service error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_order_id():
    """Generate unique order ID"""
    return f"ORDER_{uuid.uuid4().hex[:12].upper()}"


@csrf_exempt
@api_view(['POST'])
def notify_url_handler(request):
    """
    Simplified notify URL handler similar to the provided example
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            logger.info(f"Webhook notification received: {data}")
            
            # Get UniPayment credentials
            client_id = getattr(settings, 'UNIPAYMENT_CLIENT_ID', '')
            client_secret = getattr(settings, 'UNIPAYMENT_CLIENT_SECRET', '')
            
            if not client_id or not client_secret:
                return Response({'message': 'Configuration error'}, status=500)
            
            # Use NOWPayments service
            try:
                nowpayments_service = NOWPaymentsService()
                signature = request.headers.get('x-nowpayments-sig', '')
                success, response_message = nowpayments_service.handle_webhook(
                    request.body.decode('utf-8'), 
                    signature
                )
                
                if success:
                    # Update database if payment confirmed
                    payment_id = data.get('payment_id')
                    payment_status = data.get('payment_status', '')
                    
                    if payment_id and payment_status in ['finished', 'confirmed']:
                        try:
                            payment = Payment.objects.get(gateway_transaction_id=payment_id)
                            payment.status = 'completed'
                            payment.completed_at = timezone.now()
                            payment.transaction_hash = data.get('outcome_hash', data.get('pay_hash', ''))
                            payment.save()
                            logger.info(f"Payment {payment.reference} marked as completed")
                        except Payment.DoesNotExist:
                            logger.warning(f"Payment not found for payment_id: {payment_id}")
                    
                    return Response({'message': response_message})
                else:
                    return Response({'message': response_message}, status=400)
                    
            except ValueError as ve:
                logger.error(f"NOWPayments configuration error: {str(ve)}")
                return Response({'message': 'Configuration error'}, status=500)
                
            return Response({'message': 'Processed'})
            
        except Exception as e:
            logger.error(f"Error in notify handler: {str(e)}")
            return Response({'message': 'Error'}, status=500)
    
    return Response({'message': 'Method not allowed'}, status=405)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_crypto_invoice(request):
    """
    Create a NOWPayments crypto invoice
    """
    try:
        # Get data from request
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'USD')
        pay_currency = request.data.get('pay_currency', 'btc')
        plan_id = request.data.get('plan_id')  # Optional plan reference
        
        if not amount:
            return Response({
                'success': False,
                'error': 'Amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get plan if provided
        plan = None
        if plan_id:
            try:
                plan = BillingPlan.objects.get(id=plan_id)
            except BillingPlan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid plan ID'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize NOWPayments service
        try:
            nowpayments_service = NOWPaymentsService()
            
            # Generate order ID
            order_id = f"ORDER_{uuid.uuid4().hex[:12].upper()}"
            
            # Create invoice with NOWPayments
            success, result = nowpayments_service.create_invoice(
                amount=float(amount),
                currency=currency,
                order_id=order_id,
                description=f"Subscription payment for {request.user.username}",
                success_url=f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/billing/success",
                cancel_url=f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/billing/cancel",
                ipn_callback_url=get_webhook_url(request)
            )
            
            logger.info(f"NOWPayments invoice creation - Success: {success}, Result: {result}")
            
            if success:
                # Get or create a payment method for NOWPayments
                payment_method, created = PaymentMethod.objects.get_or_create(
                    payment_type='crypto_nowpayments',
                    defaults={
                        'name': 'NOWPayments Crypto',
                        'is_active': True,
                        'is_crypto': True,
                        'is_flutterwave': False
                    }
                )
                
                logger.info(f"Using payment method: {payment_method}, created: {created}")
                
                # Create payment record in database
                logger.info(f"Created payment with ID: {result.get('id', order_id)}")
                
                # Prepare gateway response data
                gateway_data = {'nowpayments_data': result}
                if plan:
                    gateway_data.update({'plan_id': str(plan.id), 'plan_name': plan.name})
                
                payment = Payment.objects.create(
                    user=request.user,
                    payment_id=result.get('id', order_id),
                    reference=f"NOW_{uuid.uuid4().hex[:8].upper()}",
                    payment_method=payment_method,
                    purpose='subscription',
                    amount_usd=amount,
                    amount_paid=amount,
                    currency=currency,
                    gateway_transaction_id=result.get('id', ''),
                    gateway_response=gateway_data,
                    status='pending'
                )
                
                logger.info(f"Created payment record: {payment.reference} for user: {request.user}")
                
                return Response({
                    'success': True,
                    'embedded_payment_data': {
                        'invoice_id': result.get('id'),
                        'payment_reference': payment.reference,
                        'order_id': order_id,
                        'invoice_url': result.get('invoice_url'),
                        'payment_url': result.get('invoice_url'),
                        'amount': float(amount),
                        'currency': currency,
                        'pay_currency': pay_currency,
                        'price_amount': result.get('price_amount', amount),
                        'price_currency': result.get('price_currency', currency),
                        'pay_amount': result.get('pay_amount', 0.0),
                        'created_at': result.get('created_at'),
                        'updated_at': result.get('updated_at'),
                        'order_description': result.get('order_description'),
                        'payment_status': result.get('payment_status', 'waiting'),
                        'success_url': result.get('success_url'),
                        'cancel_url': result.get('cancel_url'),
                        'expires_at': result.get('expires_at') or result.get('expiration_date') or result.get('expiration_estimate_date') or (timezone.now() + timezone.timedelta(hours=24)).isoformat(),
                        'status': result.get('payment_status', 'waiting')
                    }
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Failed to create invoice')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError as ve:
            return Response({
                'success': False,
                'error': 'NOWPayments configuration error',
                'details': str(ve)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Error creating crypto invoice: {str(e)}")
        return Response({
            'success': False,
            'error': 'Invoice creation failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_crypto_payment(request):
    """
    Create a crypto payment address
    """
    try:
        plan_id = request.data.get('plan_id')
        crypto_type = request.data.get('crypto_type')  # e.g., 'crypto_bitcoin', 'crypto_ethereum'
        purpose = request.data.get('purpose', 'subscription')
        
        if not plan_id or not crypto_type:
            return Response({
                'success': False,
                'error': 'Plan ID and crypto type are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        plan = get_object_or_404(BillingPlan, id=plan_id)
        
        # Get or create crypto payment method
        payment_method = PaymentMethod.objects.filter(
            payment_type=crypto_type,
            is_active=True
        ).first()
        
        if not payment_method:
            # Create a default payment method for this crypto type
            payment_method, created = PaymentMethod.objects.get_or_create(
                payment_type=crypto_type,
                defaults={
                    'name': f'NOWPayments {crypto_type.replace("crypto_", "").upper()}',
                    'is_active': True,
                    'is_crypto': True,
                    'is_flutterwave': False
                }
            )
            logger.info(f"Created payment method for {crypto_type}: {payment_method}")
        
        # Create payment with NOWPayments
        try:
            nowpayments_service = NOWPaymentsService()
            
            # Generate order ID
            order_id = f"ORDER_{uuid.uuid4().hex[:12].upper()}"
            
            # Map crypto_type to pay_currency
            pay_currency_map = {
                'crypto_bitcoin': 'btc',
                'crypto_ethereum': 'eth',
                'crypto_usdt': 'usdt',
                'crypto_usdc': 'usdc'
            }
            pay_currency = pay_currency_map.get(crypto_type, 'btc')
            
            # Create payment with NOWPayments
            success, result = nowpayments_service.create_payment(
                amount=float(plan.price),
                currency='USD',
                pay_currency=pay_currency,
                order_id=order_id,
                description=f"Subscription payment for {request.user.username} - {plan.name}",
                ipn_callback_url=get_webhook_url(request)
            )
            
            if success:
                # Create payment record in database
                logger.info(f"Created payment with ID: {result.get('id', order_id)}")
                payment = Payment.objects.create(
                    user=request.user,
                    payment_id=result.get('payment_id', order_id),
                    reference=f"NOW_{uuid.uuid4().hex[:8].upper()}",
                    payment_method=payment_method,
                    purpose=purpose,
                    amount_usd=plan.price,
                    amount_paid=result.get('pay_amount', 0),
                    currency=result.get('pay_currency', pay_currency),
                    gateway_transaction_id=result.get('payment_id', ''),
                    gateway_response={'plan_id': str(plan.id), 'plan_name': plan.name, 'nowpayments_data': result},
                    status='pending'
                )
                
                logger.info(f"Created payment record: {payment.reference} for user: {request.user}")
                
                return Response({
                    'success': True,
                    'data': {
                        'payment_reference': payment.reference,
                        'payment_address': result.get('pay_address'),
                        'amount_crypto': str(result.get('pay_amount', 0)),
                        'amount_usd': str(plan.price),
                        'currency': result.get('pay_currency', pay_currency),
                        'network': 'mainnet',
                        'expires_at': result.get('expires_at') or result.get('expiration_date') or result.get('expiration_estimate_date') or (timezone.now() + timezone.timedelta(hours=24)).isoformat(),
                        'required_confirmations': 3,
                        'qr_code_data': result.get('pay_address', ''),
                        'invoice_url': None,  # NOWPayments direct payments don't have invoice URLs
                        'payment_id': result.get('payment_id'),
                        'order_id': order_id,
                        'payment_status': result.get('payment_status', 'waiting')
                    }
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Failed to create payment'),
                    'details': result.get('details')
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as ve:
            if "API key not configured" in str(ve):
                return Response({
                    'success': False,
                    'error': 'NOWPayments not configured',
                    'details': 'Please configure NOWPAYMENTS_API_KEY environment variable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                raise ve
            
    except Exception as e:
        logger.error(f"Error creating crypto payment: {str(e)}")
        return Response({
            'success': False,
            'error': 'Crypto payment service error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_payment_status(request, reference):
    """
    Check payment status by reference
    """
    try:
        logger.info(f"Checking payment status for reference: {reference}, user: {request.user}")
        
        # First, try to find the payment without user filter to see if it exists at all
        try:
            payment_exists = Payment.objects.get(reference=reference)
            logger.info(f"Payment found for reference {reference}, but checking user match...")
        except Payment.DoesNotExist:
            logger.error(f"No payment found with reference: {reference}")
            return Response({
                'success': False,
                'error': f'Payment not found with reference: {reference}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        payment = get_object_or_404(Payment, reference=reference, user=request.user)
        
        if payment.payment_method.is_flutterwave:
            # Check Flutterwave payment
            flutterwave_service = FlutterwaveService(payment.payment_method)
            success, result = flutterwave_service.get_payment_status(reference)
        elif payment.payment_method.is_crypto:
            # Check crypto payment via NOWPayments with enhanced validation
            try:
                nowpayments_service = NOWPaymentsService()
                success, result = nowpayments_service.get_payment_status(payment.gateway_transaction_id)
                
                if success:
                    # Get payment status from NOWPayments API
                    api_payment_status = result.get('payment_status', 'waiting')
                    
                    # CRITICAL: Only update if webhook hasn't already confirmed the payment
                    # This prevents race conditions between API polling and webhook updates
                    if not payment.webhook_received:
                        logger.info(f"Updating payment {payment.reference} from API poll - status: {api_payment_status}")
                        
                        if api_payment_status in ['finished', 'confirmed'] and payment.status == 'pending':
                            payment.status = 'completed'
                            payment.completed_at = timezone.now()
                            payment.transaction_hash = result.get('outcome_hash', result.get('pay_hash', ''))
                            
                            # Mark that this was updated via API, not webhook
                            payment.gateway_response.update({'api_confirmation': True})
                            payment.save()
                            
                            logger.info(f"✅ Payment {payment.reference} confirmed via API polling")
                            
                        elif api_payment_status in ['failed', 'expired', 'refunded'] and payment.status == 'pending':
                            payment.status = 'failed' if api_payment_status != 'expired' else 'expired'
                            payment.save()
                            
                            logger.info(f"❌ Payment {payment.reference} failed via API polling - status: {api_payment_status}")
                    else:
                        logger.info(f"Payment {payment.reference} already updated by webhook - using database status")
                    
                    # Return unified status format with enhanced data
                    result = {
                        'status': payment.status,
                        'amount': str(payment.amount_usd),
                        'currency': payment.currency,
                        'transaction_hash': payment.transaction_hash,
                        'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                        'payment_status': api_payment_status,
                        'actually_paid': result.get('actually_paid'),
                        'pay_address': result.get('pay_address'),
                        'is_expired': api_payment_status in ['expired', 'failed'],
                        'webhook_received': payment.webhook_received,
                        'confirmation_source': 'webhook' if payment.webhook_received else 'api_poll'
                    }
            except ValueError as ve:
                return Response({
                    'success': False,
                    'error': 'NOWPayments not configured',
                    'details': str(ve)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            return Response({
                'success': False,
                'error': 'Unknown payment method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if success:
            return Response({
                'success': True,
                'payment': result
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to check payment status')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return Response({
            'success': False,
            'error': 'Payment status check error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_flutterwave_payment(request):
    """
    Verify Flutterwave payment after redirect
    """
    try:
        transaction_id = request.data.get('transaction_id')
        
        if not transaction_id:
            return Response({
                'success': False,
                'error': 'Transaction ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get Flutterwave payment method
        payment_method = PaymentMethod.objects.filter(
            payment_type='flutterwave',
            is_active=True
        ).first()
        
        if not payment_method:
            return Response({
                'success': False,
                'error': 'Flutterwave payment method not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify payment
        flutterwave_service = FlutterwaveService(payment_method)
        success, result = flutterwave_service.verify_payment(transaction_id)
        
        if success:
            return Response({
                'success': True,
                'verification': result
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Payment verification failed'),
                'details': result.get('details')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error verifying Flutterwave payment: {str(e)}")
        return Response({
            'success': False,
            'error': 'Payment verification error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_payment(request, reference):
    """
    Cancel a pending payment
    """
    try:
        payment = get_object_or_404(Payment, reference=reference, user=request.user)
        
        if payment.status != 'pending':
            return Response({
                'success': False,
                'error': 'Payment cannot be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if payment.payment_method.is_flutterwave:
            flutterwave_service = FlutterwaveService(payment.payment_method)
            success, result = flutterwave_service.cancel_payment(reference)
        else:
            # For crypto payments, just mark as cancelled
            payment.status = 'cancelled'
            payment.save()
            success = True
            result = {'message': 'Payment cancelled successfully'}
        
        if success:
            return Response({
                'success': True,
                'message': result.get('message', 'Payment cancelled successfully')
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to cancel payment')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error cancelling payment: {str(e)}")
        return Response({
            'success': False,
            'error': 'Payment cancellation error',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])
def test_webhook_config(request):
    """
    Test webhook URL configuration and accessibility
    """
    try:
        webhook_url = get_webhook_url(request)
        
        # Test URL accessibility
        import requests
        try:
            # Quick ping test to see if the webhook endpoint is reachable
            response = requests.get(webhook_url.replace('/webhook/', '/methods/'), timeout=5)
            url_accessible = response.status_code < 500
        except:
            url_accessible = False
        
        return Response({
            'success': True,
            'webhook_url': webhook_url,
            'backend_url_configured': bool(getattr(settings, 'BACKEND_URL', None)),
            'backend_url': getattr(settings, 'BACKEND_URL', 'Not configured'),
            'url_accessible': url_accessible,
            'nowpayments_configured': bool(getattr(settings, 'NOWPAYMENTS_API_KEY', None)),
            'ipn_secret_configured': bool(getattr(settings, 'NOWPAYMENTS_IPN_SECRET', None)),
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Webhook configuration test failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_payments(request):
    """
    Get user's payment history
    """
    try:
        payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:50]
        
        payment_data = []
        for payment in payments:
            payment_data.append({
                'reference': payment.reference,
                'purpose': payment.get_purpose_display(),
                'amount_usd': str(payment.amount_usd),
                'amount_paid': str(payment.amount_paid),
                'currency': payment.currency,
                'status': payment.get_status_display(),
                'payment_method': payment.payment_method.name,
                'created_at': payment.created_at.isoformat(),
                'completed_at': payment.completed_at.isoformat() if payment.completed_at else None,
                'transaction_hash': payment.transaction_hash if payment.is_crypto_payment else None
            })
        
        return Response({
            'success': True,
            'payments': payment_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user payments: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get payment history',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Webhook Views
@method_decorator(csrf_exempt, name='dispatch')
class FlutterwaveWebhookView(View):
    """
    Handle Flutterwave webhook notifications
    """
    
    def post(self, request):
        try:
            # Parse webhook data
            webhook_data = json.loads(request.body)
            signature = request.headers.get('verif-hash', '')
            
            # Get Flutterwave payment method
            payment_method = PaymentMethod.objects.filter(
                payment_type='flutterwave',
                is_active=True
            ).first()
            
            if not payment_method:
                logger.error("No active Flutterwave payment method found")
                return HttpResponse(status=404)
            
            # Process webhook
            flutterwave_service = FlutterwaveService(payment_method)
            success, result = flutterwave_service.process_webhook(webhook_data, signature)
            
            if success:
                logger.info(f"Flutterwave webhook processed successfully: {result}")
                return HttpResponse("OK", status=200)
            else:
                logger.error(f"Flutterwave webhook processing failed: {result}")
                return HttpResponse("Error", status=400)
                
        except Exception as e:
            logger.error(f"Error processing Flutterwave webhook: {str(e)}")
            return HttpResponse("Internal Server Error", status=500)


@api_view(['GET'])
def payment_callback(request):
    """
    Handle payment callback redirects
    """
    try:
        # Get parameters from URL
        status_param = request.GET.get('status')
        tx_ref = request.GET.get('tx_ref')
        transaction_id = request.GET.get('transaction_id')
        
        # Redirect to frontend with parameters
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        redirect_url = f"{frontend_url}/billing/callback"
        redirect_params = []
        
        if status_param:
            redirect_params.append(f"status={status_param}")
        if tx_ref:
            redirect_params.append(f"tx_ref={tx_ref}")
        if transaction_id:
            redirect_params.append(f"transaction_id={transaction_id}")
        
        if redirect_params:
            redirect_url += "?" + "&".join(redirect_params)
        
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Error in payment callback: {str(e)}")
        # Redirect to frontend error page
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return HttpResponseRedirect(f"{frontend_url}/billing/error")


# NOWPayments Webhook View
@method_decorator(csrf_exempt, name='dispatch')
class NOWPaymentsWebhookView(View):
    """
    Handle NOWPayments IPN webhook notifications
    """
    
    def post(self, request):
        try:
            # Parse webhook data
            webhook_data = json.loads(request.body)
            # logger.info(f"NOWPayments webhook received: {webhook_data}")
            
            # Get signature for verification
            signature = request.headers.get('x-nowpayments-sig', '')
            
            # Initialize NOWPayments service and handle webhook
            try:
                nowpayments_service = NOWPaymentsService()
                success, response_message = nowpayments_service.handle_webhook(
                    request.body.decode('utf-8'), 
                    signature
                )
                
                if success:
                    # Update payment status in database if needed
                    payment_id = webhook_data.get('payment_id')
                    payment_status = webhook_data.get('payment_status', '')
                    order_id = webhook_data.get('order_id')
                    logger.info(f"Processing webhook for payment_id: {payment_id}")
                    if payment_id and payment_status in ['finished', 'confirmed']:
                        try:
                            payment = Payment.objects.get(gateway_transaction_id=payment_id)
                            payment.status = 'completed'
                            payment.completed_at = timezone.now()
                            payment.transaction_hash = webhook_data.get('outcome_hash', webhook_data.get('pay_hash', ''))
                            payment.webhook_received = True  # Set webhook flag
                            payment.save()
                            
                            # Process successful payment (activate subscription, etc.)
                            self._process_successful_payment(payment)
                            
                            logger.info(f"Payment {payment.reference} completed successfully")
                            
                        except Payment.DoesNotExist:
                            logger.warning(f"Payment not found for payment_id: {payment_id}")
                    elif payment_id and payment_status in ['failed', 'expired', 'refunded']:
                        try:
                            payment = Payment.objects.get(gateway_transaction_id=payment_id)
                            payment.status = 'failed'
                            payment.webhook_received = True  # Set webhook flag
                            payment.save()
                            logger.info(f"Payment {payment.reference} marked as failed")
                        except Payment.DoesNotExist:
                            logger.warning(f"Payment not found for payment_id: {payment_id}")
                    
                    return HttpResponse(response_message, status=200)
                else:
                    logger.warning(f"NOWPayments webhook processing failed: {response_message}")
                    return HttpResponse(response_message, status=400)
                    
            except ValueError as ve:
                logger.error(f"NOWPayments configuration error: {str(ve)}")
                return HttpResponse("Configuration Error", status=500)
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook data")
            return HttpResponse("Invalid JSON", status=400)
        except Exception as e:
            logger.error(f"Error processing NOWPayments webhook: {str(e)}")
            return HttpResponse("Internal Server Error", status=500)
    
    def _send_notification_email(self, webhook_data):
        """
        Send notification email similar to the provided example
        """
        try:
            import smtplib
            from email.message import EmailMessage
            import ssl
            
            subject = "Payment Notification"
            body = f"""
            Payment Update:
            {webhook_data}
            
            Status: {webhook_data.get('status', 'Unknown')}
            Invoice ID: {webhook_data.get('invoice_id', 'Unknown')}
            Amount: {webhook_data.get('pay_amount', 'Unknown')} {webhook_data.get('pay_currency', 'USD')}
            """
            
            # Email configuration (use your own settings)
            email_sender = getattr(settings, 'EMAIL_HOST_USER', 'noreply@example.com')
            email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            recipient = getattr(settings, 'NOTIFICATION_EMAIL', 'admin@example.com')
            
            if not email_password:
                logger.warning("Email password not configured, skipping notification")
                return
            
            em = EmailMessage()
            em['From'] = email_sender
            em['To'] = recipient
            em['Subject'] = subject
            em.set_content(body)
            
            context = ssl.create_default_context()
            smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
            smtp_port = getattr(settings, 'EMAIL_PORT', 587)
            
            if smtp_port == 587:
                # Use STARTTLS
                with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                    smtp.starttls(context=context)
                    smtp.login(email_sender, email_password)
                    smtp.sendmail(email_sender, recipient, em.as_string())
            else:
                # Use SSL
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as smtp:
                    smtp.login(email_sender, email_password)
                    smtp.sendmail(email_sender, recipient, em.as_string())
                    
            logger.info("Notification email sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending notification email: {str(e)}")
            raise
    
    def _process_successful_payment(self, payment):
        """
        Process successful payment - activate subscription, etc.
        """
        try:
            if payment.purpose in ['subscription', 'upgrade']:
                # Get plan from payment data
                plan = None
                if payment.gateway_response and 'plan_id' in payment.gateway_response:
                    try:
                        plan = BillingPlan.objects.get(id=payment.gateway_response['plan_id'])
                    except BillingPlan.DoesNotExist:
                        logger.warning(f"Plan not found for payment {payment.reference}, falling back to price matching")
                
                # Fallback to price matching if no plan found
                if not plan:
                    plan = BillingPlan.objects.filter(price=payment.amount_usd).first()
                
                if not plan:
                    logger.error(f"No plan found for payment {payment.reference} with amount ${payment.amount_usd}")
                    return
                
                # Calculate next payment date based on plan interval
                from datetime import timedelta
                if plan.billing_interval == 'monthly':
                    next_payment = payment.completed_at + timedelta(days=30)
                elif plan.billing_interval == 'yearly':
                    next_payment = payment.completed_at + timedelta(days=365)
                else:  # one_time
                    next_payment = None
                
                # Get or create user subscription
                subscription, created = UserSubscription.objects.get_or_create(
                    user=payment.user,
                    defaults={
                        'plan': plan,
                        'status': 'active',
                        'last_payment_date': payment.completed_at,
                        'next_payment_date': next_payment,
                        'current_period_start': payment.completed_at,
                        'current_period_end': next_payment or payment.completed_at + timedelta(days=36500)
                    }
                )
                
                if not created:
                    # Update existing subscription
                    subscription.plan = plan
                    subscription.status = 'active'
                    subscription.last_payment_date = payment.completed_at
                    subscription.next_payment_date = next_payment
                    subscription.current_period_start = payment.completed_at
                    subscription.current_period_end = next_payment or payment.completed_at + timedelta(days=36500)
                    subscription.save()
                
                logger.info(f"Subscription activated for user {payment.user.id} with plan {plan.name}")
                
        except Exception as e:
            logger.error(f"Error processing successful payment {payment.reference}: {str(e)}")