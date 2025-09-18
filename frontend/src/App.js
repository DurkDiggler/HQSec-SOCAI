import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import AlertDetail from './pages/AlertDetail';
import Settings from './pages/Settings';
import AIDashboard from './components/AIDashboard';
import DatabaseMonitorPage from './pages/DatabaseMonitor';
import APIPerformancePage from './pages/APIPerformance';
import RealtimeConnection from './components/RealtimeConnection';
import './index.css';

function App() {
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
