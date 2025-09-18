import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { lazyLoad, preloadCriticalComponents } from './utils/lazyLoading';
import Layout from './components/Layout';
import RealtimeConnection from './components/RealtimeConnection';
import LoadingSpinner from './components/LoadingSpinner';
import './index.css';

// Lazy load pages for better performance
const Dashboard = lazyLoad(() => import('./pages/Dashboard'));
const Alerts = lazyLoad(() => import('./pages/Alerts'));
const AlertDetail = lazyLoad(() => import('./pages/AlertDetail'));
const Settings = lazyLoad(() => import('./pages/Settings'));
const AIDashboard = lazyLoad(() => import('./components/AIDashboard'));
const DatabaseMonitorPage = lazyLoad(() => import('./pages/DatabaseMonitor'));
const APIPerformancePage = lazyLoad(() => import('./pages/APIPerformance'));

function App() {
  // Preload critical components after initial load
  useEffect(() => {
    preloadCriticalComponents();
  }, []);

  const handleRealtimeAlert = (alertData) => {
    console.log('New real-time alert:', alertData);
    // You can add toast notifications or other handling here
  };

  const handleRealtimeNotification = (notificationData) => {
    console.log('New real-time notification:', notificationData);
    // You can add toast notifications or other handling here
  };

  const handleRealtimeError = (error) => {
    console.error('Real-time error:', error);
    // You can add error handling here
  };

  return (
    <Router>
      <div className="App">
        <RealtimeConnection
          onAlert={handleRealtimeAlert}
          onNotification={handleRealtimeNotification}
          onError={handleRealtimeError}
        >
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/ai" element={<AIDashboard />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/alerts/:id" element={<AlertDetail />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/database" element={<DatabaseMonitorPage />} />
            </Routes>
          </Layout>
        </RealtimeConnection>
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;
