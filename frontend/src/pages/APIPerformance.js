import React from 'react';
import APIPerformanceMonitor from '../components/APIPerformanceMonitor';

const APIPerformancePage = () => {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">API Performance Monitor</h1>
        <p className="text-gray-600 mt-1">
          Monitor API performance, caching, rate limiting, and optimization metrics
        </p>
      </div>
      
      <APIPerformanceMonitor />
    </div>
  );
};

export default APIPerformancePage;
