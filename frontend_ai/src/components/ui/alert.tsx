import React from 'react';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive';
}

interface AlertDescriptionProps extends React.HTMLAttributes<HTMLDivElement> {}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className = '', variant = 'default', ...props }, ref) => {
    const baseClasses = 'relative w-full rounded-lg border p-4 flex items-center gap-3';
    const variantClasses = {
      default: 'border-gray-200 bg-white text-gray-900',
      destructive: 'border-red-200 bg-red-50 text-red-900'
    };
    
    return (
      <div
        ref={ref}
        role="alert"
        className={`${baseClasses} ${variantClasses[variant]} ${className}`}
        {...props}
      />
    );
  }
);
Alert.displayName = 'Alert';

const AlertDescription = React.forwardRef<HTMLDivElement, AlertDescriptionProps>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`text-sm leading-relaxed ${className}`}
      {...props}
    />
  )
);
AlertDescription.displayName = 'AlertDescription';

export { Alert, AlertDescription };