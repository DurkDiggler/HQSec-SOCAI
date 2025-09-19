import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from 'react-error-boundary';
import { HelmetProvider } from 'react-helmet-async';

import { store } from './store';
import { AuthProvider } from './components/AuthProvider';
import Layout from './components/Layout';
import LoadingSpinner from './components/ui/LoadingSpinner';
import ErrorFallback from './components/ErrorFallback';
import { websocketManager } from './services/websocket';
import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Lazy load pages for better performance
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Alerts = React.lazy(() => import('./pages/Alerts'));
const AlertDetail = React.lazy(() => import('./pages/AlertDetail'));
const Metrics = React.lazy(() => import('./pages/Metrics'));
const Settings = React.lazy(() => import('./pages/Settings'));

const App: React.FC = () => {
  // Initialize WebSocket connection
  useEffect(() => {
    websocketManager.connect().catch(console.error);
    
    return () => {
      websocketManager.disconnect();
    };
  }, []);

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <HelmetProvider>
            <AuthProvider>
              <Router>
                <div className="App">
                  <Layout>
                    <Suspense fallback={<LoadingSpinner size="lg" text="Loading..." />}>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/alerts" element={<Alerts />} />
                        <Route path="/alerts/:id" element={<AlertDetail />} />
                        <Route path="/metrics" element={<Metrics />} />
                        <Route path="/settings" element={<Settings />} />
                      </Routes>
                    </Suspense>
                  </Layout>
                  <Toaster position="top-right" />
                </div>
              </Router>
            </AuthProvider>
          </HelmetProvider>
        </QueryClientProvider>
      </Provider>
    </ErrorBoundary>
  );
};

export default App;
