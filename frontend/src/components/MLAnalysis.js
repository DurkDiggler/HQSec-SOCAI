import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './Card';
import { Button } from './Button';
import { LoadingSpinner } from './LoadingSpinner';

const MLAnalysis = () => {
  const [eventData, setEventData] = useState({
    message: '',
    event_type: '',
    source: '',
    severity: 'MEDIUM',
    ip: '',
    user: ''
  });
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEventData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAnalyze = async (analysisType) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/ml/analyze/${analysisType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult({ type: analysisType, result });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleComprehensiveAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/ml/analyze/comprehensive', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData),
      });

      if (!response.ok) {
        throw new Error(`Comprehensive analysis failed: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult({ type: 'comprehensive', result });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderAnalysisResult = () => {
    if (!analysisResult) return null;

    const { type, result } = analysisResult;

    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="capitalize">
            {type.replace('_', ' ')} Analysis Result
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {type === 'comprehensive' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(result.analysis_results).map(([modelName, modelResult]) => (
                  <div key={modelName} className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-lg mb-2 capitalize">
                      {modelName.replace('_', ' ')}
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(modelResult).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-gray-600 capitalize">
                            {key.replace('_', ' ')}:
                          </span>
                          <span className="font-medium">
                            {typeof value === 'object' ? JSON.stringify(value) : 
                             typeof value === 'number' ? value.toFixed(2) : value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {Object.entries(result).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">
                      {key.replace('_', ' ')}:
                    </span>
                    <span className="font-medium">
                      {typeof value === 'object' ? JSON.stringify(value) : 
                       typeof value === 'number' ? value.toFixed(2) : value}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">ML Analysis</h1>

      <Card>
        <CardHeader>
          <CardTitle>Event Data Input</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message
              </label>
              <textarea
                name="message"
                value={eventData.message}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                rows="3"
                placeholder="Enter event message..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Event Type
              </label>
              <input
                type="text"
                name="event_type"
                value={eventData.event_type}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., authentication, network, system"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source
              </label>
              <input
                type="text"
                name="source"
                value={eventData.source}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., firewall, ids, auth_server"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Severity
              </label>
              <select
                name="severity"
                value={eventData.severity}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                IP Address
              </label>
              <input
                type="text"
                name="ip"
                value={eventData.ip}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., 192.168.1.100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                User
              </label>
              <input
                type="text"
                name="user"
                value={eventData.user}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-md"
                placeholder="e.g., admin, user@domain.com"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Options</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
            <Button
              onClick={() => handleAnalyze('anomaly')}
              disabled={loading}
              variant="outline"
            >
              Anomaly
            </Button>
            <Button
              onClick={() => handleAnalyze('risk')}
              disabled={loading}
              variant="outline"
            >
              Risk
            </Button>
            <Button
              onClick={() => handleAnalyze('classify')}
              disabled={loading}
              variant="outline"
            >
              Classify
            </Button>
            <Button
              onClick={() => handleAnalyze('filter-fp')}
              disabled={loading}
              variant="outline"
            >
              Filter FP
            </Button>
            <Button
              onClick={() => handleAnalyze('patterns')}
              disabled={loading}
              variant="outline"
            >
              Patterns
            </Button>
            <Button
              onClick={handleComprehensiveAnalysis}
              disabled={loading}
              className="bg-blue-600 text-white hover:bg-blue-700"
            >
              Comprehensive
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading && <LoadingSpinner />}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <strong>Error:</strong> {error}
        </div>
      )}

      {renderAnalysisResult()}
    </div>
  );
};

export default MLAnalysis;
