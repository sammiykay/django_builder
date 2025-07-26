# Payment Gateway Integration Setup Guide

This guide covers the complete setup of Flutterwave and cryptocurrency payment gateways for the Django AI Builder application.

## Overview

The payment system supports:
- **Flutterwave**: Credit cards, bank transfers, mobile money
- **Cryptocurrency**: Bitcoin, Ethereum, USDT, USDC

## Backend Setup

### 1. Install Dependencies

The required dependencies have been added to `requirements.txt`:
```
requests-oauthlib
rave-python
web3
eth-account
cryptography
```

Install them:
```bash
pip install -r requirements.txt
```

### 2. Database Migration

Run the migration to create payment models:
```bash
python manage.py migrate
```

### 3. Environment Configuration

Add these settings to your Django settings file:

```python
# Flutterwave Configuration
FLUTTERWAVE_PUBLIC_KEY = "your_flutterwave_public_key"
FLUTTERWAVE_SECRET_KEY = "your_flutterwave_secret_key"
FLUTTERWAVE_ENCRYPTION_KEY = "your_flutterwave_encryption_key"

# Cryptocurrency RPC URLs
ETHEREUM_MAINNET_URL = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
ETHEREUM_TESTNET_URL = "https://sepolia.infura.io/v3/YOUR_PROJECT_ID"
POLYGON_MAINNET_URL = "https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID"
BSC_MAINNET_URL = "https://bsc-dataseed.binance.org/"

# Payment Configuration
PAYMENT_CALLBACK_URL = "https://yourdomain.com/billing/callback"
PAYMENT_LOGO_URL = "https://yourdomain.com/static/logo.png"
FRONTEND_URL = "https://yourdomain.com"
```

### 4. Setup Payment Methods

Run the setup command to create default payment methods:
```bash
python manage.py setup_payments
```

### 5. Configure Webhooks

#### Flutterwave Webhook
Set up webhook URL in your Flutterwave dashboard:
```
https://yourdomain.com/api/payments/flutterwave/webhook/
```

## Frontend Setup

### 1. Components Added

- `PaymentGateway.tsx` - Main payment selection and processing component
- `CryptoPaymentWidget.tsx` - Crypto payment interface with QR codes
- Updated `SimpleBillingDashboard.tsx` - Integrated payment options

### 2. API Integration

The frontend uses these API endpoints:
- `GET /api/payments/methods/` - Get available payment methods
- `POST /api/payments/flutterwave/create/` - Create Flutterwave payment
- `POST /api/payments/crypto/create/` - Create crypto payment
- `GET /api/payments/{reference}/status/` - Check payment status

## Payment Flows

### Flutterwave Payment Flow

1. User selects plan and Flutterwave payment method
2. Frontend calls `/api/payments/flutterwave/create/`
3. Backend creates payment record and returns Flutterwave payment link
4. User completes payment in Flutterwave popup
5. Webhook receives payment confirmation
6. Backend updates payment status and activates subscription

### Crypto Payment Flow

1. User selects plan and cryptocurrency
2. Frontend calls `/api/payments/crypto/create/`
3. Backend generates unique payment address and amount
4. User sends crypto to the provided address
5. Backend monitors blockchain for confirmations
6. Payment confirmed after required confirmations
7. Subscription activated automatically

## Security Considerations

### Flutterwave
- Webhook signatures are verified using HMAC-SHA256
- API keys are stored securely in environment variables
- Payment amounts are validated on backend

### Cryptocurrency
- Private keys are encrypted before storage
- Exchange rates are fetched from reliable APIs
- Blockchain confirmations prevent double-spending
- Contract addresses are validated for token payments

## Testing

### Test Flutterwave Payments
1. Use Flutterwave test API keys
2. Use test card numbers provided by Flutterwave
3. Webhook events can be simulated in Flutterwave dashboard

### Test Crypto Payments
1. Use testnet configurations
2. Send small amounts to test addresses
3. Monitor testnet explorers for confirmations

## API Endpoints Reference

### Payment Methods
```
GET /api/payments/methods/
```
Returns available payment methods.

### Create Flutterwave Payment
```
POST /api/payments/flutterwave/create/
{
  "plan_id": 1,
  "purpose": "subscription"
}
```

### Create Crypto Payment
```
POST /api/payments/crypto/create/
{
  "plan_id": 1,
  "crypto_type": "crypto_bitcoin",
  "purpose": "subscription"
}
```

### Check Payment Status
```
GET /api/payments/{reference}/status/
```

### Verify Flutterwave Payment
```
POST /api/payments/flutterwave/verify/
{
  "transaction_id": "flw_tx_id"
}
```

### Cancel Payment
```
POST /api/payments/{reference}/cancel/
```

### Get Payment History
```
GET /api/payments/history/
```

## Database Models

### PaymentMethod
Stores configuration for each payment gateway.

### Payment
Tracks individual payment transactions.

### CryptoWallet
Manages cryptocurrency wallet addresses.

### PaymentWebhook
Logs all webhook events for auditing.

## Monitoring and Maintenance

### Payment Status Monitoring
- Set up alerts for failed payments
- Monitor webhook processing errors
- Track payment success rates

### Exchange Rate Updates
- Crypto exchange rates are updated automatically
- Consider implementing rate caching for performance

### Blockchain Monitoring
- Monitor blockchain network congestion
- Adjust required confirmations based on network conditions

## Troubleshooting

### Common Issues

1. **Flutterwave webhook not received**
   - Check webhook URL configuration
   - Verify SSL certificate
   - Check firewall settings

2. **Crypto payment not detected**
   - Verify blockchain RPC connectivity
   - Check contract addresses for tokens
   - Ensure sufficient network confirmations

3. **Payment stuck in processing**
   - Check webhook logs
   - Verify transaction on blockchain explorer
   - Manual payment confirmation may be needed

### Debug Commands

Check payment method configuration:
```bash
python manage.py shell
>>> from ai_builder.models import PaymentMethod
>>> PaymentMethod.objects.all()
```

View payment status:
```bash
python manage.py shell
>>> from ai_builder.models import Payment
>>> Payment.objects.filter(status='pending')
```

## Production Deployment

### Security Checklist
- [ ] Use HTTPS for all endpoints
- [ ] Secure webhook endpoints
- [ ] Encrypt sensitive data at rest
- [ ] Use environment variables for API keys
- [ ] Implement rate limiting
- [ ] Monitor for suspicious activity

### Performance Optimization
- [ ] Cache exchange rates
- [ ] Use database indexes for payment queries
- [ ] Implement pagination for payment history
- [ ] Optimize blockchain API calls

## Support and Documentation

- Flutterwave: https://developer.flutterwave.com/
- Web3.py: https://web3py.readthedocs.io/
- Ethereum: https://ethereum.org/developers/