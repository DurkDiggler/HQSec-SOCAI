import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from 'react-error-boundary';
import { HelmetProvider } from 'react-helmet-async';

import { store } from './store';
import { lazyLoad, preloadCriticalComponents } from './utils/lazyLoading';
import { AuthProvider } from './components/AuthProvider';
import Layout from './components/Layout';
import RealtimeConnection from './components/RealtimeConnection';
import LoadingSpinner from './components/ui/LoadingSpinner';
import ErrorFallback from './components/ErrorFallback';
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
const Dashboard = lazyLoad(() => import('./pages/Dashboard'));
const Alerts = lazyLoad(() => import('./pages/Alerts'));
const AlertDetail = lazyLoad(() => import('./pages/AlertDetail'));
const Settings = lazyLoad(() => import('./pages/Settings'));
const AIDashboard = lazyLoad(() => import('./components/AIDashboard'));
const DatabaseMonitorPage = lazyLoad(() => import('./pages/DatabaseMonitor'));
const APIPerformancePage = lazyLoad(() => import('./pages/APIPerformance'));
const FileManagerPage = lazyLoad(() => import('./pages/FileManager'));
const LogSearchPage = lazyLoad(() => import('./pages/LogSearch'));
const MetricsPage = lazyLoad(() => import('./pages/Metrics'));
const MLDashboard = lazyLoad(() => import('./components/MLDashboard'));
const MLAnalysis = lazyLoad(() => import('./components/MLAnalysis'));
const AnalyticsDashboard = lazyLoad(() => import('./components/analytics/AnalyticsDashboard'));

const App: React.FC = () => {
  // Preload critical components after initial load
  useEffect(() => {
    preloadCriticalComponents();
  }, []);

  const handleRealtimeAlert = (alertData: any) => {
    console.log('New real-time alert:', alertData);
    // You can add toast notifications or other handling here
  };

  const handleRealtimeNotification = (notificationData: any) => {
    console.log('New real-time notification:', notificationData);
    // You can add toast notifications or other handling here
  };

  const handleRealtimeError = (error: Error) => {
    console.error('Real-time error:', error);
    // You can add error handling here
  };

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <HelmetProvider>
            <AuthProvider>
              <Router>
                <div className="App">
                  <RealtimeConnection
                    onAlert={handleRealtimeAlert}
                    onNotification={handleRealtimeNotification}
                    onError={handleRealtimeError}
                  >
                    <Layout>
                      <Suspense fallback={<LoadingSpinner size="lg" text="Loading..." />}>
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/ai" element={<AIDashboard />} />
                          <Route path="/ml" element={<MLDashboard />} />
                          <Route path="/ml/analysis" element={<MLAnalysis />} />
                          <Route path="/analytics" element={<AnalyticsDashboard />} />
                          <Route path="/alerts" element={<Alerts />} />
                          <Route path="/alerts/:id" element={<AlertDetail />} />
                          <Route path="/files" element={<FileManagerPage />} />
                          <Route path="/search" element={<LogSearchPage />} />
                          <Route path="/metrics" element={<MetricsPage />} />
                          <Route path="/settings" element={<Settings />} />
                          <Route path="/database" element={<DatabaseMonitorPage />} />
                        </Routes>
                      </Suspense>
                    </Layout>
                  </RealtimeConnection>
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
