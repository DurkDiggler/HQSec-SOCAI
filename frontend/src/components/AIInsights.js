import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  TrendingUp,
  Shield,
  Target,
  Zap
} from 'lucide-react';
import { aiAPI } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

const AIInsights = ({ alertId, onAnalysisComplete }) => {
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (alertId) {
      fetchAIAnalysis();
    }
  }, [alertId]);

  const fetchAIAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await aiAPI.analyzeAlert(alertId);
      setAiAnalysis(data.ai_analysis);
      if (onAnalysisComplete) {
        onAnalysisComplete(data.ai_analysis);
      }
    } catch (err) {
      console.error('Error fetching AI analysis:', err);
      setError('Failed to load AI analysis');
      toast.error('Failed to load AI analysis');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel?.toUpperCase()) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'LOW': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner text="AI is analyzing..." />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-red-200 p-6">
        <div className="flex items-center text-red-600">
          <XCircle className="h-5 w-5 mr-2" />
          <span>{error}</span>
        </div>
        <button
          onClick={fetchAIAnalysis}
          className="mt-3 text-sm text-blue-600 hover:text-blue-800"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!aiAnalysis) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center text-gray-500">
          <Brain className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p>No AI analysis available</p>
          <button
            onClick={fetchAIAnalysis}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800"
          >
            Run AI Analysis
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Brain className="h-5 w-5 text-purple-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">AI Analysis</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getRiskLevelColor(aiAnalysis.risk_level)}`}>
            {aiAnalysis.risk_level || 'UNKNOWN'}
          </span>
          <span className={`text-sm font-medium ${getConfidenceColor(aiAnalysis.confidence_score)}`}>
            {aiAnalysis.confidence_score || 0}% confidence
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {/* Threat Classification */}
        {aiAnalysis.threat_classification && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Threat Classification</h4>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center">
                <AlertTriangle className="h-4 w-4 text-red-500 mr-2" />
                <span className="text-sm text-gray-900">{aiAnalysis.threat_classification}</span>
              </div>
            </div>
          </div>
        )}

        {/* AI Recommendations */}
        {aiAnalysis.recommendations && aiAnalysis.recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">AI Recommendations</h4>
            <div className="space-y-2">
              {aiAnalysis.recommendations.map((rec, index) => (
                <div key={index} className="flex items-start">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{rec}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Attack Vectors */}
        {aiAnalysis.attack_vectors && aiAnalysis.attack_vectors.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Potential Attack Vectors</h4>
            <div className="flex flex-wrap gap-2">
              {aiAnalysis.attack_vectors.map((vector, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full"
                >
                  {vector}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* IOCs */}
        {aiAnalysis.iocs && (aiAnalysis.iocs.ips?.length > 0 || aiAnalysis.iocs.domains?.length > 0) && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Indicators of Compromise</h4>
            <div className="space-y-2">
              {aiAnalysis.iocs.ips && aiAnalysis.iocs.ips.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-gray-500">IP Addresses:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {aiAnalysis.iocs.ips.map((ip, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                      >
                        {ip}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {aiAnalysis.iocs.domains && aiAnalysis.iocs.domains.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-gray-500">Domains:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {aiAnalysis.iocs.domains.map((domain, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded"
                      >
                        {domain}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Mitigation Strategies */}
        {aiAnalysis.mitigation_strategies && aiAnalysis.mitigation_strategies.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Mitigation Strategies</h4>
            <div className="space-y-2">
              {aiAnalysis.mitigation_strategies.map((strategy, index) => (
                <div key={index} className="flex items-start">
                  <Shield className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-gray-700">{strategy}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pattern Analysis */}
        {aiAnalysis.pattern_analysis && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Pattern Analysis</h4>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="text-sm text-gray-600">
                <div className="flex items-center justify-between">
                  <span>Threat Categories:</span>
                  <span className="font-medium">
                    {aiAnalysis.pattern_analysis.threat_categories?.join(', ') || 'None detected'}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span>Pattern Confidence:</span>
                  <span className="font-medium">
                    {aiAnalysis.pattern_analysis.confidence || 0}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <button
          onClick={fetchAIAnalysis}
          className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
        >
          <Zap className="h-4 w-4 mr-1" />
          Refresh Analysis
        </button>
      </div>
    </div>
  );
};

export default AIInsights;
