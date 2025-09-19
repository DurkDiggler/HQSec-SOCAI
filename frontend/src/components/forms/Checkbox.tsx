import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { Check } from 'lucide-react';

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  helperText?: string;
  variant?: 'default' | 'error' | 'success';
}

const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, error, helperText, variant = 'default', className, ...props }, ref) => {
    const baseClasses = 'h-4 w-4 rounded border focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';
    
    const variantClasses = {
      default: 'border-gray-300 text-blue-600 focus:ring-blue-500',
      error: 'border-red-300 text-red-600 focus:ring-red-500',
      success: 'border-green-300 text-green-600 focus:ring-green-500',
    };
    
    const checkboxClasses = clsx(
      baseClasses,
      variantClasses[variant],
      className
    );
    
    return (
      <div className="w-full">
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              ref={ref}
              type="checkbox"
              className={checkboxClasses}
              {...props}
            />
          </div>
          
          {label && (
            <div className="ml-3 text-sm">
              <label
                htmlFor={props.id}
                className="font-medium text-gray-700 cursor-pointer"
              >
                {label}
              </label>
            </div>
          )}
        </div>
        
        {error && (
          <div className="mt-1 text-sm text-red-600">
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

Checkbox.displayName = 'Checkbox';

export default Checkbox;
