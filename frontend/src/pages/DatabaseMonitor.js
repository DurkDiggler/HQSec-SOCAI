import React from 'react';
import DatabaseMonitor from '../components/DatabaseMonitor';

const DatabaseMonitorPage = () => {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Database Monitor</h1>
        <p className="text-gray-600 mt-1">
          Monitor database performance, health, and optimization metrics
        </p>
      </div>
      
      <DatabaseMonitor />
    </div>
  );
};

export default DatabaseMonitorPage;
