// Performance monitoring utilities
export const performanceMonitor = {
  // Measure component render time
  measureRender: (componentName: string, renderFn: () => any) => {
    const start = performance.now();
    const result = renderFn();
    const end = performance.now();
    console.log(`${componentName} rendered in ${end - start}ms`);
    return result;
  },

  // Measure API call performance
  measureApiCall: async (apiName: string, apiCall: () => Promise<any>) => {
    const start = performance.now();
    try {
      const result = await apiCall();
      const end = performance.now();
      console.log(`${apiName} completed in ${end - start}ms`);
      return result;
    } catch (error) {
      const end = performance.now();
      console.error(`${apiName} failed after ${end - start}ms:`, error);
      throw error;
    }
  },

  // Measure WebSocket message processing
  measureWebSocketMessage: (messageType: string, processFn: () => any) => {
    const start = performance.now();
    const result = processFn();
    const end = performance.now();
    console.log(`WebSocket ${messageType} processed in ${end - start}ms`);
    return result;
  },

  // Get memory usage
  getMemoryUsage: () => {
    if (performance.memory) {
      return {
        used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
        total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
        limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024),
      };
    }
    return null;
  },

  // Log performance metrics
  logMetrics: () => {
    const memory = performanceMonitor.getMemoryUsage();
    if (memory) {
      console.log('Memory Usage:', memory);
    }
    
    // Log Web Vitals
    if (window.performance && window.performance.getEntriesByType) {
      const paintEntries = window.performance.getEntriesByType('paint');
      paintEntries.forEach(entry => {
        console.log(`${entry.name}: ${entry.startTime}ms`);
      });
    }
  },
};

// Web Vitals measurement
export const measureWebVitals = () => {
  if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
    // Measure Largest Contentful Paint
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime);
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // Measure First Input Delay
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        console.log('FID:', entry.processingStart - entry.startTime);
      });
    }).observe({ entryTypes: ['first-input'] });

    // Measure Cumulative Layout Shift
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        if (!entry.hadRecentInput) {
          console.log('CLS:', entry.value);
        }
      });
    }).observe({ entryTypes: ['layout-shift'] });
  }
};
