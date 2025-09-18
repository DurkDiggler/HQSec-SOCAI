import { useState, useEffect, useCallback, useRef } from 'react';
import { useRealtime } from '../components/RealtimeConnection';

/**
 * Hook for auto-refreshing data with real-time updates
 */
export const useAutoRefresh = ({
  fetchFunction,
  interval = 30000, // 30 seconds default
  enabled = true,
  dependencies = [],
  onError,
  onSuccess,
  retryOnError = true,
  maxRetries = 3,
  retryDelay = 5000,
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const { isConnected } = useRealtime();
  
  const intervalRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  const isMountedRef = useRef(true);

  // Fetch data function
  const fetchData = useCallback(async (isRetry = false) => {
    if (!enabled || !fetchFunction) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await fetchFunction();
      
      if (isMountedRef.current) {
        setData(result);
        setLastUpdated(new Date());
        setRetryCount(0);
        onSuccess?.(result);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err);
        onError?.(err);
        
        if (retryOnError && retryCount < maxRetries) {
          setRetryCount(prev => prev + 1);
          retryTimeoutRef.current = setTimeout(() => {
            fetchData(true);
          }, retryDelay * Math.pow(2, retryCount)); // Exponential backoff
        }
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [enabled, fetchFunction, onError, onSuccess, retryOnError, retryCount, maxRetries, retryDelay]);

  // Start auto-refresh
  const startAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    if (enabled && interval > 0) {
      intervalRef.current = setInterval(() => {
        fetchData();
      }, interval);
    }
  }, [enabled, interval, fetchData]);

  // Stop auto-refresh
  const stopAutoRefresh = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Manual refresh
  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  // Force refresh (ignores loading state)
  const forceRefresh = useCallback(() => {
    setLoading(false);
    fetchData();
  }, [fetchData]);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchData();
    }
  }, [enabled, ...dependencies]);

  // Auto-refresh setup
  useEffect(() => {
    if (enabled && interval > 0) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }

    return () => {
      stopAutoRefresh();
    };
  }, [enabled, interval, startAutoRefresh, stopAutoRefresh]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      stopAutoRefresh();
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [stopAutoRefresh]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    retryCount,
    refresh,
    forceRefresh,
    startAutoRefresh,
    stopAutoRefresh,
    isConnected,
  };
};

/**
 * Hook for real-time data updates with WebSocket
 */
export const useRealtimeData = ({
  fetchFunction,
  realtimeChannels = [],
  enabled = true,
  dependencies = [],
  onRealtimeUpdate,
  onError,
  onSuccess,
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const { isConnected, subscribeToChannels, unsubscribeFromChannels } = useRealtime();
  
  const isMountedRef = useRef(true);

  // Fetch data function
  const fetchData = useCallback(async () => {
    if (!enabled || !fetchFunction) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await fetchFunction();
      
      if (isMountedRef.current) {
        setData(result);
        setLastUpdated(new Date());
        onSuccess?.(result);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err);
        onError?.(err);
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [enabled, fetchFunction, onError, onSuccess]);

  // Handle real-time updates
  const handleRealtimeUpdate = useCallback((updateData) => {
    if (onRealtimeUpdate) {
      const newData = onRealtimeUpdate(data, updateData);
      if (newData !== undefined) {
        setData(newData);
        setLastUpdated(new Date());
      }
    } else {
      // Default behavior: refresh data on real-time update
      fetchData();
    }
  }, [data, onRealtimeUpdate, fetchData]);

  // Subscribe to real-time channels
  useEffect(() => {
    if (enabled && isConnected && realtimeChannels.length > 0) {
      subscribeToChannels(realtimeChannels);
    }

    return () => {
      if (realtimeChannels.length > 0) {
        unsubscribeFromChannels(realtimeChannels);
      }
    };
  }, [enabled, isConnected, realtimeChannels, subscribeToChannels, unsubscribeFromChannels]);

  // Listen for real-time messages
  useEffect(() => {
    if (enabled && isConnected) {
      const handleMessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (realtimeChannels.some(channel => message.channel === channel)) {
            handleRealtimeUpdate(message.data);
          }
        } catch (err) {
          console.error('Failed to parse real-time message:', err);
        }
      };

      // This would need to be connected to the actual WebSocket
      // For now, we'll use the existing realtime context
    }
  }, [enabled, isConnected, realtimeChannels, handleRealtimeUpdate]);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchData();
    }
  }, [enabled, ...dependencies]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return {
    data,
    loading,
    error,
    lastUpdated,
    isConnected,
    refresh: fetchData,
  };
};

/**
 * Hook for paginated data with auto-refresh
 */
export const usePaginatedAutoRefresh = ({
  fetchFunction,
  pageSize = 20,
  interval = 30000,
  enabled = true,
  dependencies = [],
  onError,
  onSuccess,
}) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [lastUpdated, setLastUpdated] = useState(null);
  const { isConnected } = useRealtime();
  
  const intervalRef = useRef(null);
  const isMountedRef = useRef(true);

  // Fetch data function
  const fetchData = useCallback(async (page = 1, append = false) => {
    if (!enabled || !fetchFunction) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await fetchFunction(page, pageSize);
      
      if (isMountedRef.current) {
        if (append) {
          setData(prev => [...prev, ...result.data]);
        } else {
          setData(result.data);
        }
        setHasMore(result.hasMore);
        setCurrentPage(page);
        setLastUpdated(new Date());
        onSuccess?.(result);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err);
        onError?.(err);
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [enabled, fetchFunction, pageSize, onError, onSuccess]);

  // Load more data
  const loadMore = useCallback(() => {
    if (hasMore && !loading) {
      fetchData(currentPage + 1, true);
    }
  }, [hasMore, loading, currentPage, fetchData]);

  // Refresh current data
  const refresh = useCallback(() => {
    fetchData(1, false);
  }, [fetchData]);

  // Auto-refresh setup
  useEffect(() => {
    if (enabled && interval > 0) {
      intervalRef.current = setInterval(() => {
        refresh();
      }, interval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, interval, refresh]);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchData(1, false);
    }
  }, [enabled, ...dependencies]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return {
    data,
    loading,
    error,
    hasMore,
    currentPage,
    lastUpdated,
    isConnected,
    loadMore,
    refresh,
  };
};

export default useAutoRefresh;
