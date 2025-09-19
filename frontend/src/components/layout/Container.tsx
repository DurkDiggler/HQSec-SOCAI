import React from 'react';
import { clsx } from 'clsx';
import type { BaseComponentProps } from '../../types';

interface ContainerProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  center?: boolean;
}

const Container: React.FC<ContainerProps> = ({
  children,
  size = 'lg',
  padding = 'md',
  center = true,
  className,
}) => {
  const sizeClasses = {
    sm: 'max-w-2xl',
    md: 'max-w-4xl',
    lg: 'max-w-6xl',
    xl: 'max-w-7xl',
    full: 'max-w-full',
  };

  const paddingClasses = {
    none: '',
    sm: 'px-4',
    md: 'px-6',
    lg: 'px-8',
  };

  const classes = clsx(
    'w-full',
    sizeClasses[size],
    paddingClasses[padding],
    center && 'mx-auto',
    className
  );

  return (
    <div className={classes}>
      {children}
    </div>
  );
};

export default Container;
