import React, { useState, useEffect } from 'react';
import { CreditCard, Bitcoin, Shield, Clock, CheckCircle, AlertCircle, Copy, ExternalLink } from 'lucide-react';
import { apiService } from '../../services/api';
import NOWPaymentWidget from './NOWPaymentWidget';
import CryptoPaymentWidget from './CryptoPaymentWidget';

interface PaymentMethod {
  id: number;
  name: string;
  payment_type: string;
  is_active: boolean;
  is_crypto: boolean;
  is_flutterwave: boolean;
  crypto_symbol?: string;
  crypto_network?: string;
  usd_exchange_rate?: string;
}

interface BillingPlan {
  id: number;
  name: string;
  price: string;
  billing_interval: string;
  token_limit: number;
  description: string;
}

interface PaymentGatewayProps {
  selectedPlan: BillingPlan;
  onPaymentSuccess: () => void;
  onClose: () => void;
}

interface FlutterwavePayment {
  payment_link: string;
  payment_reference: string;
  amount: string;
  currency: string;
  expires_at: string;
}

interface CryptoPayment {
  payment_address: string;
  amount_crypto: string;
  amount_usd: string;
  currency: string;
  network: string;
  payment_reference: string;
  expires_at: string;
  required_confirmations: number;
  contract_address?: string;
  qr_code_data: string;
  payment_url?: string;  // UniPayment invoice URL
  invoice_url?: string;  // UniPayment invoice URL (alternative)
  invoice_id?: string;   // UniPayment invoice ID
  order_id?: string;     // UniPayment order ID
  explorer_url?: string; // Blockchain explorer URL
}

interface NOWPaymentData {
  invoice_id?: string;
  payment_id?: string;
  payment_reference: string;
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
  status: string;
}

const PaymentGateway: React.FC<PaymentGatewayProps> = ({ selectedPlan, onPaymentSuccess, onClose }) => {
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Payment states
  const [flutterwavePayment, setFlutterwavePayment] = useState<FlutterwavePayment | null>(null);
  const [cryptoPayment, setCryptoPayment] = useState<CryptoPayment | null>(null);
  const [nowPaymentData, setNowPaymentData] = useState<NOWPaymentData | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'creating' | 'pending' | 'completed' | 'failed'>('idle');
  const [statusCheckInterval, setStatusCheckInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadPaymentMethods();
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, []);

  const loadPaymentMethods = async () => {
    try {
      setLoading(true);
      const response = await apiService.getPaymentMethods();
      if (response.success) {
        setPaymentMethods(response.payment_methods);
      } else {
        setError('Failed to load payment methods');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load payment methods');
    } finally {
      setLoading(false);
    }
  };

  const createFlutterwavePayment = async () => {
    if (!selectedMethod) return;
    
    try {
      setPaymentStatus('creating');
      setError(null);
      
      const response = await apiService.createFlutterwavePayment(selectedPlan.id, 'subscription');
      
      if (response.success) {
        const paymentData = response.data as FlutterwavePayment;
        setFlutterwavePayment(paymentData);
        setPaymentStatus('pending');
        
        // Open Flutterwave popup
        window.open(paymentData.payment_link, '_blank');
        
        // Start checking payment status
        startStatusCheck(paymentData.payment_reference);
      } else {
        setError(response.data.error || 'Failed to create payment');
        setPaymentStatus('failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Payment creation failed');
      setPaymentStatus('failed');
    }
  };

  const createCryptoPayment = async () => {
    if (!selectedMethod) return;
    
    try {
      setPaymentStatus('creating');
      setError(null);
      
      const response = await apiService.createCryptoPayment(selectedPlan.id, selectedMethod.payment_type, 'subscription');
      
      if (response.success) {
        const paymentData = response.data as CryptoPayment;
        setCryptoPayment(paymentData);
        setPaymentStatus('pending');
        
        // Start checking payment status
        startStatusCheck(paymentData.payment_reference);
      } else {
        setError(response.data.error || 'Failed to create crypto payment');
        setPaymentStatus('failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Crypto payment creation failed');
      setPaymentStatus('failed');
    }
  };

  const createNOWPaymentInvoice = async () => {
    if (!selectedMethod) return;
    
    try {
      setPaymentStatus('creating');
      setError(null);
      
      const response = await apiService.post('/api/payments/crypto/invoice/', {
        amount: parseFloat(selectedPlan.price),
        currency: 'USD',
        pay_currency: 'btc' // Default to BTC, can be made configurable
      });
      
      if (response.data.success) {
        const paymentData = response.data.embedded_payment_data as NOWPaymentData;
        setNowPaymentData(paymentData);
        setPaymentStatus('pending');
        
        // Start checking payment status
        startStatusCheck(paymentData.payment_reference);
      } else {
        setError(response.data.error || 'Failed to create NOWPayments invoice');
        setPaymentStatus('failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'NOWPayments invoice creation failed');
      setPaymentStatus('failed');
    }
  };

  const startStatusCheck = (reference: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await apiService.checkPaymentStatus(reference);
        if (response.success) {
          const status = response.payment.status;
          
          if (status === 'completed') {
            setPaymentStatus('completed');
            clearInterval(interval);
            setTimeout(onPaymentSuccess, 2000); // Show success for 2 seconds
          } else if (status === 'failed' || status === 'cancelled' || status === 'expired') {
            setPaymentStatus('failed');
            clearInterval(interval);
            setError('Payment failed or expired');
          }
        }
      } catch (err) {
        console.error('Status check error:', err);
      }
    }, 5000); // Check every 5 seconds
    
    setStatusCheckInterval(interval);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getPaymentMethodIcon = (method: PaymentMethod) => {
    if (method.is_flutterwave) {
      return <CreditCard className="w-6 h-6" />;
    } else if (method.is_crypto) {
      switch (method.crypto_symbol) {
        case 'BTC':
          return <Bitcoin className="w-6 h-6 text-orange-500" />;
        case 'ETH':
          return <div className="w-6 h-6 bg-gradient-to-r from-purple-400 to-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">ETH</div>;
        case 'USDT':
          return <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold">₮</div>;
        case 'USDC':
          return <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">$</div>;
        default:
          return <Bitcoin className="w-6 h-6" />;
      }
    }
    return <Shield className="w-6 h-6" />;
  };

  const getPaymentMethodDescription = (method: PaymentMethod) => {
    if (method.is_flutterwave) {
      return 'Credit Card, Bank Transfer, Mobile Money';
    } else if (method.is_crypto) {
      const networkName = method.crypto_network ? 
        method.crypto_network.charAt(0).toUpperCase() + method.crypto_network.slice(1) 
        : 'Mainnet';
      const rateInfo = method.usd_exchange_rate ? 
        ` • ~$${parseFloat(method.usd_exchange_rate).toFixed(2)}` 
        : '';
      return `${method.crypto_symbol} • ${networkName} Network${rateInfo}`;
    }
    return method.name;
  };

  // Group payment methods by type for better UI
  const groupedPaymentMethods = () => {
    const flutterwaveMethods = paymentMethods.filter(m => m.is_flutterwave);
    const cryptoMethods = paymentMethods.filter(m => m.is_crypto);
    const otherMethods = paymentMethods.filter(m => !m.is_flutterwave && !m.is_crypto);
    
    return { flutterwaveMethods, cryptoMethods, otherMethods };
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-gray-600 dark:text-gray-300">Loading payment methods...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Complete Payment
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                {selectedPlan.name} - ${selectedPlan.price}/{selectedPlan.billing_interval}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700 dark:text-red-300">{error}</span>
              </div>
            </div>
          )}

          {paymentStatus === 'idle' && (
            <>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Choose Payment Method
              </h3>
              
              <div className="space-y-6">
                {/* Traditional Payment Methods */}
                {groupedPaymentMethods().flutterwaveMethods.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center">
                      <CreditCard className="w-4 h-4 mr-2" />
                      Traditional Payments
                    </h4>
                    <div className="space-y-2">
                      {groupedPaymentMethods().flutterwaveMethods.map((method) => (
                        <div
                          key={method.id}
                          className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                            selectedMethod?.id === method.id
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                          onClick={() => setSelectedMethod(method)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <div className="text-gray-600 dark:text-gray-300 mr-3">
                                {getPaymentMethodIcon(method)}
                              </div>
                              <div>
                                <h5 className="font-medium text-gray-900 dark:text-white">
                                  {method.name}
                                </h5>
                                <p className="text-sm text-gray-600 dark:text-gray-300">
                                  {getPaymentMethodDescription(method)}
                                </p>
                              </div>
                            </div>
                            <div className={`w-4 h-4 rounded-full border-2 ${
                              selectedMethod?.id === method.id
                                ? 'border-blue-500 bg-blue-500'
                                : 'border-gray-300 dark:border-gray-600'
                            }`}>
                              {selectedMethod?.id === method.id && (
                                <div className="w-full h-full rounded-full bg-white transform scale-50"></div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cryptocurrency Payment Methods */}
                {groupedPaymentMethods().cryptoMethods.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center">
                      <Bitcoin className="w-4 h-4 mr-2" />
                      Cryptocurrency
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {groupedPaymentMethods().cryptoMethods.map((method) => (
                        <div
                          key={method.id}
                          className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                            selectedMethod?.id === method.id
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                          onClick={() => setSelectedMethod(method)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <div className="mr-3">
                                {getPaymentMethodIcon(method)}
                              </div>
                              <div>
                                <h5 className="font-medium text-gray-900 dark:text-white">
                                  {method.crypto_symbol}
                                </h5>
                                <p className="text-xs text-gray-600 dark:text-gray-300">
                                  {method.crypto_network?.charAt(0).toUpperCase() + (method.crypto_network?.slice(1) || '')}
                                </p>
                                {method.usd_exchange_rate && (
                                  <p className="text-xs text-green-600 dark:text-green-400">
                                    ~${parseFloat(method.usd_exchange_rate).toFixed(2)}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className={`w-4 h-4 rounded-full border-2 ${
                              selectedMethod?.id === method.id
                                ? 'border-blue-500 bg-blue-500'
                                : 'border-gray-300 dark:border-gray-600'
                            }`}>
                              {selectedMethod?.id === method.id && (
                                <div className="w-full h-full rounded-full bg-white transform scale-50"></div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Other Payment Methods */}
                {groupedPaymentMethods().otherMethods.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-3">
                      Other Methods
                    </h4>
                    <div className="space-y-2">
                      {groupedPaymentMethods().otherMethods.map((method) => (
                        <div
                          key={method.id}
                          className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                            selectedMethod?.id === method.id
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                          onClick={() => setSelectedMethod(method)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <div className="text-gray-600 dark:text-gray-300 mr-3">
                                {getPaymentMethodIcon(method)}
                              </div>
                              <div>
                                <h5 className="font-medium text-gray-900 dark:text-white">
                                  {method.name}
                                </h5>
                                <p className="text-sm text-gray-600 dark:text-gray-300">
                                  {getPaymentMethodDescription(method)}
                                </p>
                              </div>
                            </div>
                            <div className={`w-4 h-4 rounded-full border-2 ${
                              selectedMethod?.id === method.id
                                ? 'border-blue-500 bg-blue-500'
                                : 'border-gray-300 dark:border-gray-600'
                            }`}>
                              {selectedMethod?.id === method.id && (
                                <div className="w-full h-full rounded-full bg-white transform scale-50"></div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={() => {
                  if (selectedMethod?.is_flutterwave) {
                    createFlutterwavePayment();
                  } else if (selectedMethod?.payment_type === 'crypto_nowpayments') {
                    createNOWPaymentInvoice();
                  } else {
                    createCryptoPayment();
                  }
                }}
                disabled={!selectedMethod}
                className="w-full mt-6 py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
              >
                Continue to Payment
              </button>
            </>
          )}

          {paymentStatus === 'creating' && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-300">Creating payment...</p>
            </div>
          )}

          {paymentStatus === 'pending' && flutterwavePayment && (
            <div className="text-center py-8">
              <Clock className="w-12 h-12 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Payment in Progress
              </h3>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                Complete your payment in the opened window. This page will update automatically.
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Payment Reference: {flutterwavePayment.payment_reference}
              </p>
            </div>
          )}

          {paymentStatus === 'pending' && nowPaymentData && (
            <div className="py-4">
              <NOWPaymentWidget
                paymentReference={nowPaymentData.payment_reference}
                paymentData={nowPaymentData}
                onPaymentComplete={() => {
                  setPaymentStatus('completed');
                  setTimeout(onPaymentSuccess, 2000);
                }}
                onPaymentFailed={(error) => {
                  setPaymentStatus('failed');
                  setError(error);
                }}
              />
            </div>
          )}

          {paymentStatus === 'pending' && cryptoPayment && (
            <div className="py-4">
              <CryptoPaymentWidget
                paymentReference={cryptoPayment.payment_reference}
                paymentData={{
                  payment_address: cryptoPayment.payment_address || '',
                  amount_crypto: cryptoPayment.amount_crypto || '0',
                  amount_usd: cryptoPayment.amount_usd || '0',
                  currency: cryptoPayment.currency || 'USDT',
                  network: cryptoPayment.network || 'mainnet',
                  exchange_rate: "1.0", // Default exchange rate
                  expires_at: cryptoPayment.expires_at || new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
                  required_confirmations: cryptoPayment.required_confirmations || 3,
                  contract_address: cryptoPayment.contract_address,
                  qr_code_data: cryptoPayment.qr_code_data || '',
                  invoice_url: cryptoPayment.invoice_url || cryptoPayment.payment_url,
                  invoice_id: cryptoPayment.invoice_id,
                  order_id: cryptoPayment.order_id,
                }}
                onPaymentComplete={() => {
                  setPaymentStatus('completed');
                  setTimeout(onPaymentSuccess, 2000);
                }}
                onPaymentFailed={(error) => {
                  setPaymentStatus('failed');
                  setError(error);
                }}
              />
            </div>
          )}

          {paymentStatus === 'completed' && (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Payment Successful!
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Your subscription has been activated. Redirecting...
              </p>
            </div>
          )}

          {paymentStatus === 'failed' && (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Payment Failed
              </h3>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {error || 'Something went wrong with your payment. Please try again.'}
              </p>
              <button
                onClick={() => {
                  setPaymentStatus('idle');
                  setError(null);
                  setFlutterwavePayment(null);
                  setCryptoPayment(null);
                  setNowPaymentData(null);
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaymentGateway;