import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  ExternalLink, 
  RotateCcw,
  Calendar,
  DollarSign,
  CreditCard,
  Filter,
  Download
} from 'lucide-react';
import { apiService } from '../../services/api';

interface Payment {
  reference: string;
  purpose: string;
  amount_usd: string;
  amount_paid: string;
  currency: string;
  status: string;
  payment_method: string;
  created_at: string;
  completed_at?: string;
  transaction_hash?: string;
}

interface PaymentHistoryProps {
  className?: string;
}

const PaymentHistory: React.FC<PaymentHistoryProps> = ({ className = '' }) => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getUserPayments();
      
      if (response && response.success) {
        setPayments(response.payments || []);
      } else {
        setError(response?.error || 'Failed to fetch payment history');
      }
    } catch (err) {
      console.error('Error fetching payments:', err);
      setError('Failed to load payment history');
    } finally {
      setLoading(false);
    }
  };

  const refreshPayments = async () => {
    setRefreshing(true);
    await fetchPayments();
    setRefreshing(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'paid':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
      case 'cancelled':
      case 'canceled':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'pending':
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-500 animate-pulse" />;
      case 'expired':
        return <AlertCircle className="w-5 h-5 text-orange-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'paid':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
      case 'cancelled':
      case 'canceled':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'pending':
      case 'processing':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'expired':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPaymentMethodIcon = (method: string) => {
    if (method.toLowerCase().includes('crypto') || method.toLowerCase().includes('nowpayments')) {
      return '₿';
    } else if (method.toLowerCase().includes('flutterwave')) {
      return '💳';
    }
    return '💰';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredPayments = payments.filter(payment => {
    if (filter === 'all') return true;
    return payment.status.toLowerCase() === filter.toLowerCase();
  });

  const getStatusCounts = () => {
    const counts = {
      all: payments.length,
      completed: 0,
      pending: 0,
      failed: 0,
      expired: 0
    };

    payments.forEach(payment => {
      const status = payment.status.toLowerCase();
      if (status === 'completed' || status === 'paid') {
        counts.completed++;
      } else if (status === 'pending' || status === 'processing') {
        counts.pending++;
      } else if (status === 'failed' || status === 'cancelled' || status === 'canceled') {
        counts.failed++;
      } else if (status === 'expired') {
        counts.expired++;
      }
    });

    return counts;
  };

  const statusCounts = getStatusCounts();

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <CreditCard className="w-6 h-6 text-gray-600 dark:text-gray-300" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Payment History
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={refreshPayments}
              disabled={refreshing}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Refresh payments"
            >
              <RotateCcw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex flex-wrap gap-2">
          {[
            { key: 'all', label: 'All', count: statusCounts.all },
            { key: 'completed', label: 'Completed', count: statusCounts.completed },
            { key: 'pending', label: 'Pending', count: statusCounts.pending },
            { key: 'failed', label: 'Failed', count: statusCounts.failed },
            { key: 'expired', label: 'Expired', count: statusCounts.expired }
          ].map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                filter === key
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {label} ({count})
            </button>
          ))}
        </div>
      </div>

      {/* Payment List */}
      <div className="p-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-700">{error}</span>
            </div>
          </div>
        )}

        {filteredPayments.length === 0 ? (
          <div className="text-center py-8">
            <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {filter === 'all' ? 'No payments yet' : `No ${filter} payments`}
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {filter === 'all' 
                ? 'Your payment history will appear here once you make your first payment.'
                : `You don't have any ${filter} payments.`
              }
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredPayments.map((payment) => (
              <div
                key={payment.reference}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {/* Payment Method Icon */}
                    <div className="flex-shrink-0 w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-lg">
                      {getPaymentMethodIcon(payment.payment_method)}
                    </div>

                    {/* Payment Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {payment.purpose}
                        </h4>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(payment.status)}`}>
                          {getStatusIcon(payment.status)}
                          <span className="ml-1">{payment.status}</span>
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <div className="flex items-center space-x-1">
                          <DollarSign className="w-4 h-4" />
                          <span>${payment.amount_usd}</span>
                          {payment.amount_paid !== payment.amount_usd && (
                            <span className="text-xs">
                              ({payment.amount_paid} {payment.currency})
                            </span>
                          )}
                        </div>

                        <div className="flex items-center space-x-1">
                          <Calendar className="w-4 h-4" />
                          <span>{formatDate(payment.created_at)}</span>
                        </div>

                        <div className="flex items-center space-x-1">
                          <CreditCard className="w-4 h-4" />
                          <span>{payment.payment_method}</span>
                        </div>

                        <div className="flex items-center space-x-1 font-mono text-xs">
                          <span>Ref: {payment.reference}</span>
                        </div>
                      </div>

                      {payment.completed_at && (
                        <div className="mt-2 text-xs text-green-600 dark:text-green-400">
                          Completed: {formatDate(payment.completed_at)}
                        </div>
                      )}

                      {payment.transaction_hash && (
                        <div className="mt-2">
                          <div className="flex items-center space-x-1 text-xs text-blue-600 dark:text-blue-400">
                            <span>Transaction:</span>
                            <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">
                              {payment.transaction_hash.slice(0, 16)}...
                            </code>
                            <button
                              onClick={() => navigator.clipboard.writeText(payment.transaction_hash!)}
                              className="hover:text-blue-800 dark:hover:text-blue-200"
                              title="Copy transaction hash"
                            >
                              📋
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Amount */}
                  <div className="text-right">
                    <div className="text-lg font-semibold text-gray-900 dark:text-white">
                      ${payment.amount_usd}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {payment.currency}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentHistory;