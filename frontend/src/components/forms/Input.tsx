import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { AlertCircle } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'error' | 'success';
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightIcon, variant = 'default', className, ...props }, ref) => {
    const baseClasses = 'block w-full rounded-md border px-3 py-2 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';
    
    const variantClasses = {
      default: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
      error: 'border-red-300 focus:border-red-500 focus:ring-red-500',
      success: 'border-green-300 focus:border-green-500 focus:ring-green-500',
    };
    
    const inputClasses = clsx(
      baseClasses,
      variantClasses[variant],
      leftIcon && 'pl-10',
      rightIcon && 'pr-10',
      className
    );
    
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              {leftIcon}
            </div>
          )}
          
          <input
            ref={ref}
            className={inputClasses}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              {rightIcon}
            </div>
          )}
        </div>
        
        {error && (
          <div className="mt-1 flex items-center text-sm text-red-600">
            <AlertCircle className="w-4 h-4 mr-1" />
            {error}
          </div>
        )}
        
        {helperText && !error && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
