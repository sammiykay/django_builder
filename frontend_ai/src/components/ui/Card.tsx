import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  elevated?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  onClick?: () => void;
  interactive?: boolean;
}

const Card: React.FC<CardProps> = ({
  children,
  className = '',
  elevated = false,
  padding = 'md',
  onClick,
  interactive = false,
}) => {
  const baseClasses = [
    'card',
    elevated && 'card-elevated',
    interactive && 'cursor-pointer hover:shadow-lg transition-slow',
    onClick && 'cursor-pointer',
  ].filter(Boolean);

  const paddingClasses = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const classes = [
    ...baseClasses,
    paddingClasses[padding],
    className,
  ].filter(Boolean).join(' ');

  const Component = onClick ? 'button' : 'div';

  return (
    <Component
      className={classes}
      onClick={onClick}
      type={onClick ? 'button' : undefined}
    >
      {children}
    </Component>
  );
};

export default Card;