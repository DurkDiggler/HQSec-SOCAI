import React, { Suspense, lazy } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * Higher-order component for lazy loading with error boundaries
 */
export const withLazyLoading = (Component, fallback = <LoadingSpinner />) => {
  return (props) => (
    <Suspense fallback={fallback}>
      <Component {...props} />
    </Suspense>
  );
};

/**
 * Lazy load components with error boundary
 */
export const lazyLoad = (importFunc, fallback = <LoadingSpinner />) => {
  const LazyComponent = lazy(importFunc);
  return withLazyLoading(LazyComponent, fallback);
};

/**
 * Preload components for better UX
 */
export const preloadComponent = (importFunc) => {
  return () => {
    importFunc();
  };
};

/**
 * Lazy load with intersection observer for better performance
 */
export const lazyLoadWithIntersection = (importFunc, options = {}) => {
  const defaultOptions = {
    rootMargin: '50px',
    threshold: 0.1,
    ...options,
  };

  return React.forwardRef((props, ref) => {
    const [isVisible, setIsVisible] = React.useState(false);
    const [Component, setComponent] = React.useState(null);
    const elementRef = React.useRef();

    React.useEffect(() => {
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting && !Component) {
            setIsVisible(true);
            importFunc().then((module) => {
              setComponent(() => module.default);
            });
          }
        },
        defaultOptions
      );

      if (elementRef.current) {
        observer.observe(elementRef.current);
      }

      return () => {
        if (elementRef.current) {
          observer.unobserve(elementRef.current);
        }
      };
    }, [Component]);

    if (Component) {
      return <Component {...props} ref={ref} />;
    }

    return (
      <div ref={elementRef} style={{ minHeight: '200px' }}>
        <LoadingSpinner />
      </div>
    );
  });
};

/**
 * Lazy load images with intersection observer
 */
export const LazyImage = ({ src, alt, placeholder, ...props }) => {
  const [isLoaded, setIsLoaded] = React.useState(false);
  const [isInView, setIsInView] = React.useState(false);
  const imgRef = React.useRef();

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '50px' }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  React.useEffect(() => {
    if (isInView && src) {
      const img = new Image();
      img.onload = () => setIsLoaded(true);
      img.src = src;
    }
  }, [isInView, src]);

  return (
    <div ref={imgRef} {...props}>
      {isLoaded ? (
        <img src={src} alt={alt} />
      ) : (
        placeholder || <div style={{ backgroundColor: '#f0f0f0', minHeight: '200px' }} />
      )}
    </div>
  );
};

/**
 * Lazy load with retry mechanism
 */
export const lazyLoadWithRetry = (importFunc, maxRetries = 3) => {
  return lazy(() =>
    importFunc().catch((error) => {
      if (maxRetries > 0) {
        console.warn(`Failed to load component, retrying... (${maxRetries} retries left)`);
        return lazyLoadWithRetry(importFunc, maxRetries - 1)();
      }
      throw error;
    })
  );
};

/**
 * Preload critical components
 */
export const preloadCriticalComponents = () => {
  // Preload critical components after initial load
  setTimeout(() => {
    import('../pages/Dashboard');
    import('../pages/Alerts');
    import('../components/Layout');
  }, 2000);
};

export default {
  withLazyLoading,
  lazyLoad,
  preloadComponent,
  lazyLoadWithIntersection,
  LazyImage,
  lazyLoadWithRetry,
  preloadCriticalComponents,
};
