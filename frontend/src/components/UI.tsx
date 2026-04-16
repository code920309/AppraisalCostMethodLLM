import React, { ReactNode } from 'react';
import { cn } from '../lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ title, subtitle, children, className, ...props }) => {
  return (
    <div 
      className={cn(
        "bg-white p-5 overflow-hidden flex flex-col",
        className
      )} 
      {...props}
    >
      {(title || subtitle) && (
        <div className="panel-title">
          <span>{title}</span>
          {subtitle && <span className="opacity-70">{subtitle}</span>}
        </div>
      )}
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  asChild?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  size = 'md', 
  isLoading, 
  children, 
  className, 
  disabled,
  asChild,
  ...props 
}) => {
  const variants = {
    primary: 'bg-brand-accent text-white hover:bg-brand-accent-dark font-semibold',
    secondary: 'bg-white text-brand-text-main border border-brand-border hover:bg-brand-bg font-semibold',
    outline: 'border border-brand-border bg-white text-brand-text-sub hover:bg-brand-bg',
    ghost: 'text-brand-text-sub hover:bg-brand-bg',
    danger: 'bg-brand-danger text-white hover:opacity-90 font-semibold',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-md',
    md: 'px-4 py-2.5 text-sm rounded-md',
    lg: 'px-6 py-3 text-base rounded-md',
  };

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center transition-all focus:outline-none disabled:opacity-50 disabled:pointer-events-none cursor-pointer',
        variants[variant],
        sizes[size],
        className
      )}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {children}
    </button>
  );
};

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        className={cn(
          "flex h-10 w-full rounded-md border border-brand-border bg-white px-3 py-2 text-sm placeholder:text-brand-text-sub focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-accent disabled:cursor-not-allowed disabled:opacity-50 transition-all",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
