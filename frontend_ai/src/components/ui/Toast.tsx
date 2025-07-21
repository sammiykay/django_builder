import React, { useState, useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';

interface ToastProps {
  message: string;
  type?: 'error' | 'success' | 'warning' | 'info';
  duration?: number;
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ 
  message, 
  type = 'error', 
  duration = 5000, 
  onClose 
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300); // Wait for animation to complete
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getToastStyles = () => {
    const baseStyles = "fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform transition-all duration-300 flex items-center space-x-3 max-w-md";
    
    if (!isVisible) {
      return `${baseStyles} translate-x-full opacity-0`;
    }

    switch (type) {
      case 'error':
        return `${baseStyles} bg-red-900/90 border border-red-500 text-red-200 translate-x-0 opacity-100`;
      case 'success':
        return `${baseStyles} bg-green-900/90 border border-green-500 text-green-200 translate-x-0 opacity-100`;
      case 'warning':
        return `${baseStyles} bg-yellow-900/90 border border-yellow-500 text-yellow-200 translate-x-0 opacity-100`;
      case 'info':
        return `${baseStyles} bg-blue-900/90 border border-blue-500 text-blue-200 translate-x-0 opacity-100`;
      default:
        return `${baseStyles} bg-gray-900/90 border border-gray-500 text-gray-200 translate-x-0 opacity-100`;
    }
  };

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300);
  };

  return (
    <div className={getToastStyles()}>
      <AlertCircle className="w-5 h-5 flex-shrink-0" />
      <p className="text-sm flex-1">{message}</p>
      <button
        onClick={handleClose}
        className="text-current hover:opacity-70 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export default Toast;