import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { Button } from './Button';
import { LoadingSpinner } from './LoadingSpinner';

const MLDashboard = () => {
  const [models, setModels] = useState({});
  const [performance, setPerformance] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMLData();
  }, []);

  const loadMLData = async () => {
    try {
      setLoading(true);
      const [modelsResponse, performanceResponse] = await Promise.all([
        fetch('/api/v1/ml/models/status'),
        fetch('/api/v1/ml/models/performance')
      ]);

      if (!modelsResponse.ok || !performanceResponse.ok) {
        throw new Error('Failed to load ML data');
      }

      const modelsData = await modelsResponse.json();
      const performanceData = await performanceResponse.json();

      setModels(modelsData);
      setPerformance(performanceData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadModels = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/ml/models/load', { method: 'POST' });
      
      if (!response.ok) {
        throw new Error('Failed to load models');
      }

      await loadMLData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanupModels = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/ml/models/cleanup', { method: 'POST' });
      
      if (!response.ok) {
        throw new Error('Failed to cleanup models');
      }

      await loadMLData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'unknown': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (isTrained) => {
    return isTrained ? '✅' : '❌';
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <strong>Error:</strong> {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">ML Model Dashboard</h1>
        <div className="space-x-2">
          <Button onClick={handleLoadModels} disabled={loading}>
            Load Models
          </Button>
          <Button onClick={handleCleanupModels} disabled={loading} variant="secondary">
            Cleanup Models
          </Button>
          <Button onClick={loadMLData} disabled={loading} variant="outline">
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(models).map(([modelName, modelInfo]) => (
          <Card key={modelName}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="capitalize">{modelName.replace('_', ' ')}</span>
                <span className="text-2xl">{getStatusIcon(modelInfo.is_trained)}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Status:</span>
                  <span className={`text-sm font-medium ${getStatusColor(modelInfo.training_status)}`}>
                    {modelInfo.training_status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Trained:</span>
                  <span className="text-sm font-medium">
                    {modelInfo.is_trained ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Training:</span>
                  <span className="text-sm font-medium">
                    {modelInfo.last_training === 'Never' ? 'Never' : 
                     new Date(modelInfo.last_training).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(performance).map(([modelName, metrics]) => (
              <div key={modelName} className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold text-lg mb-2 capitalize">
                  {modelName.replace('_', ' ')}
                </h3>
                <div className="space-y-1">
                  {Object.entries(metrics).map(([metricName, value]) => (
                    <div key={metricName} className="flex justify-between text-sm">
                      <span className="text-gray-600 capitalize">
                        {metricName.replace('_', ' ')}:
                      </span>
                      <span className="font-medium">
                        {typeof value === 'number' ? value.toFixed(2) : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MLDashboard;
