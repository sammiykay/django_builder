import React, { useState, useEffect } from 'react';
import { Bitcoin, Clock, CheckCircle, AlertCircle, Copy, ExternalLink, Wallet, Shield, QrCode } from 'lucide-react';
import { apiService } from '../../services/api';

interface NOWPaymentWidgetProps {
  paymentReference: string;
  paymentData: {
    invoice_id?: string;
    payment_id?: string;
    order_id: string;
    invoice_url?: string;
    payment_url?: string;
    payment_address?: string;
    amount: number;
    currency: string;
    pay_currency?: string;
    pay_amount?: number;
    price_amount?: number;
    price_currency?: string;
    payment_status?: string;
    expires_at?: string;
    created_at?: string;
    updated_at?: string;
    order_description?: string;
    success_url?: string;
    cancel_url?: string;
  };
  onPaymentComplete: () => void;
  onPaymentFailed: (error: string) => void;
}

interface PaymentStatus {
  status: string;
  amount: string;
  currency: string;
  transaction_hash?: string;
  completed_at?: string;
  payment_status?: string;
  actually_paid?: number;
  pay_address?: string;
  is_expired: boolean;
  webhook_received?: boolean;
  confirmation_source?: 'webhook' | 'api_poll';
}

const NOWPaymentWidget: React.FC<NOWPaymentWidgetProps> = ({
  paymentReference,
  paymentData,
  onPaymentComplete,
  onPaymentFailed
}) => {
  const [status, setStatus] = useState<PaymentStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<string>('');

  useEffect(() => {
    // Initial status check
    checkPaymentStatus();
    
    // Set up polling for status updates
    const statusInterval = setInterval(checkPaymentStatus, 15000); // Check every 15 seconds
    
    // Set up timer for expiration if we have expires_at
    const timerInterval = paymentData.expires_at ? setInterval(updateTimer, 1000) : null;
    
    return () => {
      clearInterval(statusInterval);
      if (timerInterval) clearInterval(timerInterval);
    };
  }, [paymentReference]);

  const checkPaymentStatus = async () => {
    try {
      setLoading(true);
      const response = await apiService.get(`/api/payments/status/${paymentReference}/`);
      
      if (response.data.success) {
        const statusData = response.data.payment as PaymentStatus;
        setStatus(statusData);
        
        // CRITICAL FIX: Only trigger completion for webhook-confirmed payments
        // This prevents premature success notifications from API polling
        if (statusData.status === 'completed' || statusData.payment_status === 'finished') {
          const isWebhookConfirmed = (statusData as any).webhook_received;
          const confirmationSource = (statusData as any).confirmation_source;
          
          console.log(`Payment status check: ${statusData.status}/${statusData.payment_status}, webhook_received: ${isWebhookConfirmed}, source: ${confirmationSource}`);
          
          // Only auto-complete if confirmed by webhook OR if explicitly confirmed by API with high confidence
          if (isWebhookConfirmed || confirmationSource === 'webhook') {
            console.log('✅ Payment confirmed by webhook - triggering completion');
            setTimeout(() => onPaymentComplete(), 2000);
          } else {
            console.log('⏳ Payment confirmed by API polling only - waiting for webhook confirmation');
            // Don't auto-complete yet, keep polling for webhook confirmation
          }
        } else if (statusData.status === 'failed' || statusData.is_expired || statusData.payment_status === 'failed') {
          onPaymentFailed(statusData.is_expired ? 'Payment expired' : 'Payment failed');
        }
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateTimer = () => {
    if (!paymentData.expires_at) return;
    
    const now = new Date().getTime();
    const expiry = new Date(paymentData.expires_at).getTime();
    const difference = expiry - now;
    
    if (difference > 0) {
      const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((difference % (1000 * 60)) / 1000);
      
      setTimeLeft(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    } else {
      setTimeLeft('EXPIRED');
      onPaymentFailed('Payment expired');
    }
  };

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const getCryptoIcon = () => {
    const currency = paymentData.pay_currency || paymentData.currency;
    switch (currency?.toLowerCase()) {
      case 'btc':
        return <Bitcoin className="w-8 h-8 text-orange-500" />;
      case 'eth':
        return <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">ETH</div>;
      case 'usdt':
        return <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold">USDT</div>;
      case 'usdc':
        return <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">USDC</div>;
      default:
        return <Wallet className="w-8 h-8 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    if (!status) return 'text-gray-500';
    
    const currentStatus = status.payment_status || status.status;
    switch (currentStatus) {
      case 'completed':
      case 'finished':
      case 'confirmed':
        return 'text-green-500';
      case 'waiting':
      case 'confirming':
      case 'processing':
        return 'text-blue-500';
      case 'failed':
      case 'expired':
      case 'refunded':
        return 'text-red-500';
      default:
        return 'text-yellow-500';
    }
  };

  const getStatusIcon = () => {
    if (!status) return <Clock className="w-5 h-5" />;
    
    const currentStatus = status.payment_status || status.status;
    switch (currentStatus) {
      case 'completed':
      case 'finished':
      case 'confirmed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'waiting':
      case 'confirming':
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
      case 'expired':
      case 'refunded':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          {getCryptoIcon()}
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              NOWPayments - {paymentData.pay_currency || paymentData.currency}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Cryptocurrency Payment
            </p>
          </div>
        </div>
        
        {timeLeft && timeLeft !== 'EXPIRED' && (
          <div className="text-right">
            <p className="text-sm text-gray-600 dark:text-gray-300">Expires in</p>
            <p className="text-lg font-mono font-bold text-red-500">{timeLeft}</p>
          </div>
        )}
      </div>

      {/* Payment Amount */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Amount to pay</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white font-mono">
            {paymentData.pay_amount || paymentData.amount} {paymentData.pay_currency || paymentData.currency}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
            ≈ ${paymentData.price_amount || paymentData.amount} {paymentData.price_currency || 'USD'}
          </p>
        </div>
      </div>

      {/* NOWPayments Invoice URL - Primary Payment Option */}
      {(paymentData.invoice_url || paymentData.payment_url) && (
        <div className="mb-6">
          <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 border-2 border-green-200 dark:border-green-700 rounded-lg p-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <ExternalLink className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-bold text-green-900 dark:text-green-100 mb-2">
                Pay with NOWPayments Interface
              </h3>
              <p className="text-green-700 dark:text-green-300 mb-4">
                Access the complete payment interface with multiple cryptocurrency options
              </p>
              <a
                href={paymentData.invoice_url || paymentData.payment_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors text-lg"
              >
                <ExternalLink className="w-5 h-5 mr-2" />
                Open Payment Interface
              </a>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {paymentData.invoice_id && (
                  <div>
                    <p className="text-green-600 dark:text-green-400 font-medium">Invoice ID</p>
                    <p className="font-mono text-green-800 dark:text-green-200">{paymentData.invoice_id}</p>
                  </div>
                )}
                {paymentData.order_id && (
                  <div>
                    <p className="text-green-600 dark:text-green-400 font-medium">Order ID</p>
                    <p className="font-mono text-green-800 dark:text-green-200">{paymentData.order_id}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Address (if available) */}
      {(status?.pay_address || paymentData.payment_address) && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Payment Address
          </label>
          <div className="flex items-center space-x-2">
            <div className="flex-1 p-3 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg">
              <code className="text-sm font-mono break-all text-gray-900 dark:text-white">
                {status?.pay_address || paymentData.payment_address}
              </code>
            </div>
            <button
              onClick={() => copyToClipboard(status?.pay_address || paymentData.payment_address!, 'address')}
              className="p-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
              title="Copy address"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
          {copied === 'address' && (
            <p className="text-sm text-green-600 dark:text-green-400 mt-1">Address copied!</p>
          )}
        </div>
      )}

      {/* Payment Status */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Payment Status</span>
          {loading && <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>}
        </div>
        
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className={`font-medium ${getStatusColor()}`}>
            {status ? (status.payment_status || status.status).charAt(0).toUpperCase() + (status.payment_status || status.status).slice(1) : 'Waiting for payment...'}
          </span>
          {status && status.webhook_received && (
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
              Webhook Confirmed
            </span>
          )}
          {status && status.confirmation_source === 'api_poll' && (
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
              API Confirmed
            </span>
          )}
        </div>
        
        {status?.transaction_hash && (
          <div className="mt-2">
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Transaction Hash:</p>
            <div className="flex items-center space-x-2">
              <code className="text-sm font-mono text-blue-600 dark:text-blue-400 break-all">
                {status.transaction_hash}
              </code>
              <button
                onClick={() => copyToClipboard(status.transaction_hash!, 'hash')}
                className="text-blue-500 hover:text-blue-600 dark:hover:text-blue-400"
                title="Copy transaction hash"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
            {copied === 'hash' && (
              <p className="text-sm text-green-600 dark:text-green-400 mt-1">Hash copied!</p>
            )}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Shield className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-2">Payment Instructions:</p>
            <ul className="space-y-1 list-disc list-inside">
              {(paymentData.invoice_url || paymentData.payment_url) && (
                <li>Click "Open Payment Interface" above for the best payment experience</li>
              )}
              <li>Payment will be confirmed automatically by the blockchain network</li>
              <li>Use a wallet you control (not an exchange) for sending payments</li>
              <li>Status updates are monitored in real-time</li>
              {timeLeft && timeLeft !== 'EXPIRED' && (
                <li>Payment expires in {timeLeft} - complete before expiration</li>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* Real-time Status Indicator */}
      <div className="mt-4 flex items-center justify-center space-x-2 text-sm text-gray-600 dark:text-gray-300">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span>Real-time monitoring via NOWPayments</span>
      </div>
    </div>
  );
};

export default NOWPaymentWidget;