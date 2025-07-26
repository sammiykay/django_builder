import uuid
import json
import logging
import requests
import hashlib
import hmac
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)


class NOWPaymentsService:
    """
    NOWPayments service for handling cryptocurrency payments
    """
    
    def __init__(self):
        # NOWPayments API configuration - SECURE
        self.api_key = getattr(settings, 'NOWPAYMENTS_API_KEY', '')
        self.ipn_secret = getattr(settings, 'NOWPAYMENTS_IPN_SECRET', '')
        self.base_url = getattr(settings, 'NOWPAYMENTS_BASE_URL', 'https://api.nowpayments.io/v1')
        self.sandbox = getattr(settings, 'NOWPAYMENTS_SANDBOX', True)
        
        if self.sandbox:
            self.base_url = 'https://api-sandbox.nowpayments.io/v1'
        
        # Validate required credentials
        if not self.api_key:
            raise ValueError("NOWPayments API key not configured. Please set NOWPAYMENTS_API_KEY environment variable.")
        if not self.ipn_secret:
            raise ValueError("NOWPayments IPN secret not configured. Please set NOWPAYMENTS_IPN_SECRET environment variable.")
        
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_available_currencies(self) -> Tuple[bool, List[str]]:
        """
        Get list of available currencies for payments
        """
        try:
            response = requests.get(f"{self.base_url}/currencies", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                currencies = data.get('currencies', [])
                return True, currencies
            else:
                logger.error(f"Failed to get currencies: {response.status_code} - {response.text}")
                return False, []
                
        except Exception as e:
            logger.error(f"Error getting available currencies: {str(e)}")
            return False, []
    
    def get_estimate(self, amount: float, currency_from: str = 'USD', currency_to: str = 'btc') -> Tuple[bool, Dict[str, Any]]:
        """
        Get estimated price for conversion
        """
        try:
            params = {
                'amount': amount,
                'currency_from': currency_from,
                'currency_to': currency_to
            }
            
            response = requests.get(f"{self.base_url}/estimate", params=params, headers=self.headers)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                logger.error(f"Failed to get estimate: {response.status_code} - {response.text}")
                return False, {"error": "Failed to get price estimate"}
                
        except Exception as e:
            logger.error(f"Error getting estimate: {str(e)}")
            return False, {"error": str(e)}
    
    def create_payment(self, amount: float, currency: str = 'USD', pay_currency: str = 'btc', 
                      order_id: str = None, description: str = '', 
                      ipn_callback_url: str = None, success_url: str = None,
                      cancel_url: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Create a payment
        """
        try:
            if not order_id:
                order_id = str(uuid.uuid4())
            
            payload = {
                'price_amount': amount,
                'price_currency': currency,
                'pay_currency': pay_currency,
                'order_id': order_id,
                'order_description': description or f"Payment for order {order_id}",
            }
            
            # Add optional parameters
            if ipn_callback_url:
                payload['ipn_callback_url'] = ipn_callback_url
            if success_url:
                payload['success_url'] = success_url
            if cancel_url:
                payload['cancel_url'] = cancel_url
            
            response = requests.post(f"{self.base_url}/payment", json=payload, headers=self.headers)
            print(response.status_code, response.text)  # Debugging line
            if response.status_code == 201:
                payment_data = response.json()
                logger.info(f"NOWPayments payment response: {payment_data}")
                
                
                return True, payment_data
            else:
                logger.error(f"Failed to create payment: {response.status_code} - {response.text}")
                return False, {"error": f"Payment creation failed: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return False, {"error": str(e)}
    
    def create_invoice(self, amount: float, currency: str = 'USD', 
                      order_id: str = None, description: str = '',
                      success_url: str = None, cancel_url: str = None,
                      ipn_callback_url: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Create an invoice with payment page
        """
        try:
            if not order_id:
                order_id = str(uuid.uuid4())
            
            payload = {
                'price_amount': amount,
                'price_currency': currency,
                'order_id': order_id,
                'order_description': description or f"Invoice for order {order_id}",
            }
            
            # Add optional parameters
            if success_url:
                payload['success_url'] = success_url
            if cancel_url:
                payload['cancel_url'] = cancel_url
            if ipn_callback_url:
                payload['ipn_callback_url'] = ipn_callback_url
            
            response = requests.post(f"{self.base_url}/invoice", json=payload, headers=self.headers)
            
            if response.status_code == 201:
                invoice_data = response.json()
                logger.info(f"NOWPayments invoice response: {invoice_data}")
                
                # Add expiration time if not provided (NOWPayments typically gives 24 hours)
                if 'expires_at' not in invoice_data and 'expiration_date' not in invoice_data:
                    from datetime import datetime, timedelta
                    expiry_time = datetime.utcnow() + timedelta(hours=24)
                    invoice_data['expires_at'] = expiry_time.isoformat() + 'Z'
                
                return True, invoice_data
            else:
                logger.error(f"Failed to create invoice: {response.status_code} - {response.text}")
                return False, {"error": f"Invoice creation failed: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            return False, {"error": str(e)}
    
    def get_payment_status(self, payment_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get payment status by payment ID
        """
        try:
            response = requests.get(f"{self.base_url}/payment/{payment_id}", headers=self.headers)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                logger.error(f"Failed to get payment status: {response.status_code} - {response.text}")
                return False, {"error": "Failed to get payment status"}
                
        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            return False, {"error": str(e)}
    
    def get_invoice_status(self, invoice_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get invoice status by invoice ID
        """
        try:
            response = requests.get(f"{self.base_url}/invoice/{invoice_id}", headers=self.headers)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                logger.error(f"Failed to get invoice status: {response.status_code} - {response.text}")
                return False, {"error": "Failed to get invoice status"}
                
        except Exception as e:
            logger.error(f"Error getting invoice status: {str(e)}")
            return False, {"error": str(e)}
    
    def verify_ipn_signature(self, payload: str, signature: str) -> bool:
        """
        Verify IPN signature from NOWPayments webhook
        """
        if not self.ipn_secret:
            logger.warning("IPN secret not configured")
            return False
        
        try:
            expected_signature = hmac.new(
                self.ipn_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying IPN signature: {str(e)}")
            return False
    
    def handle_webhook(self, payload: str, signature: str = None) -> Tuple[bool, str]:
        """
        Handle NOWPayments IPN webhook with enhanced security and validation
        """
        try:
            # Always verify signature if we have IPN secret configured
            if self.ipn_secret:
                if not signature:
                    logger.warning("Webhook received without signature but IPN secret is configured")
                    return False, "Missing signature"
                    
                if not self.verify_ipn_signature(payload, signature):
                    logger.warning("Invalid IPN signature - possible security breach attempt")
                    return False, "Invalid signature"
                    
                logger.info("Webhook signature verified successfully")
            else:
                logger.warning("IPN secret not configured - webhook security is compromised")
            
            # Parse the webhook data
            webhook_data = json.loads(payload)
            
            payment_id = webhook_data.get('payment_id')
            payment_status = webhook_data.get('payment_status')
            order_id = webhook_data.get('order_id')
            actually_paid = webhook_data.get('actually_paid')
            outcome_hash = webhook_data.get('outcome_hash')
            
            logger.info(f"Received verified IPN: Payment {payment_id}, Status: {payment_status}, Order: {order_id}, Paid: {actually_paid}")
            
            # Validate required fields
            if not payment_id or not payment_status:
                logger.error("Webhook missing required fields: payment_id or payment_status")
                return False, "Missing required fields"
            
            # Handle different payment statuses with enhanced logging
            if payment_status in ['finished', 'confirmed']:
                logger.info(f"✅ Payment {payment_id} CONFIRMED for order {order_id} - Amount paid: {actually_paid}")
                return True, "Payment confirmed"
            elif payment_status in ['failed', 'expired', 'refunded']:
                logger.info(f"❌ Payment {payment_id} FAILED/EXPIRED for order {order_id} - Status: {payment_status}")
                return True, "Payment failed"
            elif payment_status in ['waiting', 'confirming', 'sending']:
                logger.info(f"⏳ Payment {payment_id} in progress for order {order_id} - Status: {payment_status}")
                return True, "Payment in progress"
            else:
                logger.info(f"⚠️  Payment {payment_id} unknown status: {payment_status} for order {order_id}")
                return True, "Status updated"
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {str(e)}")
            return False, "Invalid JSON"
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return False, str(e)
    
    def get_minimum_payment_amount(self, currency: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get minimum payment amount for a currency
        """
        try:
            response = requests.get(f"{self.base_url}/min-amount", 
                                  params={'currency_from': 'USD', 'currency_to': currency}, 
                                  headers=self.headers)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                logger.error(f"Failed to get minimum amount: {response.status_code} - {response.text}")
                return False, {"error": "Failed to get minimum amount"}
                
        except Exception as e:
            logger.error(f"Error getting minimum amount: {str(e)}")
            return False, {"error": str(e)}