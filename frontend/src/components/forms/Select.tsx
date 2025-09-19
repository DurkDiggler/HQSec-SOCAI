import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { ChevronDown, AlertCircle } from 'lucide-react';

interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  variant?: 'default' | 'error' | 'success';
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helperText, options, placeholder, variant = 'default', className, ...props }, ref) => {
    const baseClasses = 'block w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none bg-white';
    
    const variantClasses = {
      default: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
      error: 'border-red-300 focus:border-red-500 focus:ring-red-500',
      success: 'border-green-300 focus:border-green-500 focus:ring-green-500',
    };
    
    const selectClasses = clsx(
      baseClasses,
      variantClasses[variant],
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
          <select
            ref={ref}
            className={selectClasses}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </div>
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

Select.displayName = 'Select';

export default Select;
