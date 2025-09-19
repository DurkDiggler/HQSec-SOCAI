import React from 'react';
import { clsx } from 'clsx';
import type { BaseComponentProps } from '../../types';

interface CardProps extends BaseComponentProps {
  title?: string;
  subtitle?: string;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  border?: boolean;
  hover?: boolean;
}

const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  header,
  footer,
  padding = 'md',
  shadow = 'md',
  border = true,
  hover = false,
  className,
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
  };

  const classes = clsx(
    'bg-white rounded-lg',
    border && 'border border-gray-200',
    shadowClasses[shadow],
    hover && 'hover:shadow-lg transition-shadow duration-200',
    className
  );

  const contentClasses = clsx(
    paddingClasses[padding]
  );

  return (
    <div className={classes}>
      {(title || subtitle || header) && (
        <div className="border-b border-gray-200 px-6 py-4">
          {header || (
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
              )}
            </div>
          )}
        </div>
      )}
      
      <div className={contentClasses}>
        {children}
      </div>
      
      {footer && (
        <div className="border-t border-gray-200 px-6 py-4">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
