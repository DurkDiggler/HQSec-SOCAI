import { lazy, ComponentType } from 'react';

// Lazy load components with error boundaries
export const lazyLoad = <T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) => {
  return lazy(importFunc);
};

// Preload critical components
export const preloadCriticalComponents = () => {
  // Preload dashboard components
  import('../pages/Dashboard');
  import('../components/RealtimeMetrics');
  import('../components/RealtimeNotifications');
  
  // Preload common components
  import('../components/ui/Button');
  import('../components/ui/LoadingSpinner');
  import('../components/layout/Card');
};

// Lazy load with retry
export const lazyLoadWithRetry = <T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  retries = 3
) => {
  return lazy(() => {
    return importFunc().catch((error) => {
      if (retries > 0) {
        console.warn(`Failed to load component, retrying... (${retries} retries left)`);
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve(lazyLoadWithRetry(importFunc, retries - 1)());
          }, 1000);
        });
      }
      throw error;
    });
  });
};

// Preload components on hover
export const preloadOnHover = (importFunc: () => Promise<any>) => {
  let preloaded = false;
  
  return {
    onMouseEnter: () => {
      if (!preloaded) {
        preloaded = true;
        importFunc();
      }
    },
  };
};
