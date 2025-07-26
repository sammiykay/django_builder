import React, { useState, useEffect } from 'react';
import { Bitcoin, Clock, CheckCircle, AlertCircle, Copy, ExternalLink, Wallet, Shield } from 'lucide-react';
import { apiService } from '../../services/api';

interface CryptoPaymentWidgetProps {
  paymentReference: string;
  paymentData: {
    payment_address: string;
    amount_crypto: string;
    amount_usd: string;
    currency: string;
    network: string;
    exchange_rate: string;
    expires_at: string;
    required_confirmations: number;
    contract_address?: string;
    qr_code_data: string;
    invoice_url?: string;
    invoice_id?: string;
    order_id?: string;
  };
  onPaymentComplete: () => void;
  onPaymentFailed: (error: string) => void;
}

interface PaymentStatus {
  status: string;
  confirmations: number;
  required_confirmations: number;
  transaction_hash?: string;
  amount_received?: string;
  expires_at?: string;
  is_expired: boolean;
}

const CryptoPaymentWidget: React.FC<CryptoPaymentWidgetProps> = ({
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
    const statusInterval = setInterval(checkPaymentStatus, 10000); // Check every 10 seconds
    
    // Set up timer for expiration
    const timerInterval = setInterval(updateTimer, 1000);
    
    return () => {
      clearInterval(statusInterval);
      clearInterval(timerInterval);
    };
  }, [paymentReference]);

  const checkPaymentStatus = async () => {
    try {
      setLoading(true);
      const response = await apiService.get(`/api/payments/status/${paymentReference}/`);
      
      if (response.data.success) {
        const statusData = response.data.payment as PaymentStatus;
        setStatus(statusData);
        
        if (statusData.status === 'completed') {
          setTimeout(() => onPaymentComplete(), 2000);
        } else if (statusData.status === 'failed' || statusData.is_expired) {
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
    switch (paymentData.currency) {
      case 'BTC':
        return <Bitcoin className="w-8 h-8 text-orange-500" />;
      case 'ETH':
        return <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">ETH</div>;
      case 'USDT':
        return <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold">USDT</div>;
      case 'USDC':
        return <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">USDC</div>;
      default:
        return <Wallet className="w-8 h-8 text-gray-500" />;
    }
  };

  const getExplorerUrl = (txHash: string) => {
    const baseUrls: { [key: string]: string } = {
      'mainnet': 'https://etherscan.io/tx/',
      'polygon': 'https://polygonscan.com/tx/',
      'bsc': 'https://bscscan.com/tx/',
      'testnet': 'https://sepolia.etherscan.io/tx/'
    };
    
    if (paymentData.currency === 'BTC') {
      return `https://blockstream.info/tx/${txHash}`;
    }
    
    const baseUrl = baseUrls[paymentData.network || 'mainnet'] || baseUrls['mainnet'];
    return `${baseUrl}${txHash}`;
  };

  const getStatusColor = () => {
    if (!status) return 'text-gray-500';
    
    switch (status.status) {
      case 'completed':
        return 'text-green-500';
      case 'processing':
        return 'text-blue-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-yellow-500';
    }
  };

  const getStatusIcon = () => {
    if (!status) return <Clock className="w-5 h-5" />;
    
    switch (status.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'failed':
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
              {paymentData.currency} Payment
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {paymentData.network ? (paymentData.network.charAt(0).toUpperCase() + paymentData.network.slice(1)) : 'Unknown'} Network
            </p>
          </div>
        </div>
        
        {timeLeft !== 'EXPIRED' && (
          <div className="text-right">
            <p className="text-sm text-gray-600 dark:text-gray-300">Expires in</p>
            <p className="text-lg font-mono font-bold text-red-500">{timeLeft}</p>
          </div>
        )}
      </div>

      {/* Payment Amount */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Send exactly</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white font-mono">
            {paymentData.amount_crypto} {paymentData.currency}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
            ≈ ${paymentData.amount_usd} USD
          </p>
        </div>
      </div>

      {/* UniPayment Invoice URL - Primary Payment Option */}
      {paymentData.invoice_url && (
        <div className="mb-6">
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border-2 border-purple-200 dark:border-purple-700 rounded-lg p-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <ExternalLink className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-bold text-purple-900 dark:text-purple-100 mb-2">
                Pay with Multiple Crypto Options
              </h3>
              <p className="text-purple-700 dark:text-purple-300 mb-4">
                Access the complete UniPayment interface with multiple cryptocurrencies and networks
              </p>
              <a
                href={paymentData.invoice_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors text-lg"
              >
                <ExternalLink className="w-5 h-5 mr-2" />
                Open UniPayment Interface
              </a>
              {paymentData.invoice_id && (
                <p className="text-sm text-purple-600 dark:text-purple-400 mt-3">
                  Invoice ID: {paymentData.invoice_id}
                </p>
              )}
            </div>
          </div>
          
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              ⬆️ <strong>Recommended:</strong> Use the UniPayment interface above for the best experience
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              Or continue below to send crypto directly to the wallet address
            </p>
          </div>
        </div>
      )}

      {/* Payment Address */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Payment Address
        </label>
        <div className="flex items-center space-x-2">
          <div className="flex-1 p-3 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg">
            <code className="text-sm font-mono break-all text-gray-900 dark:text-white">
              {paymentData.payment_address}
            </code>
          </div>
          <button
            onClick={() => copyToClipboard(paymentData.payment_address, 'address')}
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

      {/* Contract Address for Tokens */}
      {paymentData.contract_address && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Token Contract Address
          </label>
          <div className="flex items-center space-x-2">
            <div className="flex-1 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-800 rounded-lg">
              <code className="text-sm font-mono break-all text-yellow-800 dark:text-yellow-200">
                {paymentData.contract_address}
              </code>
            </div>
            <button
              onClick={() => copyToClipboard(paymentData.contract_address!, 'contract')}
              className="p-3 text-yellow-600 hover:text-yellow-700 dark:hover:text-yellow-300 hover:bg-yellow-100 dark:hover:bg-yellow-800/30 rounded-lg transition-colors"
              title="Copy contract address"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
          {copied === 'contract' && (
            <p className="text-sm text-green-600 dark:text-green-400 mt-1">Contract address copied!</p>
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
            {status ? status.status.charAt(0).toUpperCase() + status.status.slice(1) : 'Waiting for payment...'}
          </span>
        </div>
        
        {status && status.status === 'processing' && (
          <div className="mt-2">
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300 mb-1">
              <span>Confirmations</span>
              <span>{status.confirmations} / {status.required_confirmations}</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(status.confirmations / status.required_confirmations) * 100}%` }}
              ></div>
            </div>
          </div>
        )}
        
        {status?.transaction_hash && (
          <div className="mt-2">
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">Transaction Hash:</p>
            <div className="flex items-center space-x-2">
              <code className="text-sm font-mono text-blue-600 dark:text-blue-400 break-all">
                {status.transaction_hash}
              </code>
              <a
                href={getExplorerUrl(status.transaction_hash)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-600 dark:hover:text-blue-400"
                title="View on blockchain explorer"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Shield className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-medium mb-2">Important Instructions:</p>
            <ul className="space-y-1 list-disc list-inside">
              <li>Send exactly {paymentData.amount_crypto} {paymentData.currency} to the address above</li>
              <li>Payment will be confirmed after {paymentData.required_confirmations} network confirmations</li>
              <li>Do not send from an exchange - use a wallet you control</li>
              {paymentData.contract_address && (
                <li>Make sure to use the correct token contract address</li>
              )}
              <li>Payment expires in {timeLeft} - send before expiration</li>
            </ul>
          </div>
        </div>
      </div>

      {/* QR Code placeholder - In a real implementation, you'd generate an actual QR code */}
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
          Scan QR code with your wallet
        </p>
        <div className="inline-block p-4 bg-white border-2 border-gray-300 rounded-lg">
          <div className="w-32 h-32 bg-gray-100 rounded flex items-center justify-center">
            <span className="text-xs text-gray-500">QR Code</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CryptoPaymentWidget;