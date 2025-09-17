import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  TrendingUp, 
  AlertTriangle, 
  Shield, 
  Target,
  Zap,
  Activity,
  BarChart3,
  PieChart
} from 'lucide-react';
import { aiAPI, mcpAPI } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

const AIDashboard = () => {
  const [aiInsights, setAiInsights] = useState(null);
  const [threatCorrelations, setThreatCorrelations] = useState(null);
  const [mcpStatus, setMcpStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAIData();
  }, []);

  const fetchAIData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch MCP status
      const mcpData = await mcpAPI.getStatus();
      setMcpStatus(mcpData.mcp_servers);
      
      // Simulate AI insights (in real implementation, this would come from AI analysis)
      setAiInsights({
        totalThreats: 47,
        aiAnalyzed: 42,
        highConfidence: 38,
        criticalThreats: 3,
        attackCampaigns: 2,
        falsePositives: 5,
        aiRecommendations: 12,
        automatedResponses: 8
      });
      
      // Simulate threat correlations
      setThreatCorrelations({
        activeCampaigns: [
          {
            id: 1,
            name: "APT Campaign Alpha",
            threatCount: 15,
            confidence: 92,
            status: "active",
            lastSeen: "2 hours ago"
          },
          {
            id: 2,
            name: "Credential Stuffing Wave",
            threatCount: 8,
            confidence: 87,
            status: "monitoring",
            lastSeen: "4 hours ago"
          }
        ],
        topThreats: [
          { type: "Malware", count: 12, trend: "up" },
          { type: "Phishing", count: 8, trend: "down" },
          { type: "Brute Force", count: 6, trend: "up" },
          { type: "Lateral Movement", count: 4, trend: "stable" }
        ]
      });
      
    } catch (err) {
      console.error('Error fetching AI data:', err);
      setError('Failed to load AI dashboard data');
      toast.error('Failed to load AI dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'down':
        return <TrendingUp className="h-4 w-4 text-green-500 rotate-180" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getCampaignStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'monitoring':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'resolved':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner text="Loading AI dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-400 mr-2" />
          <span className="text-red-800">{error}</span>
        </div>
        <button
          onClick={fetchAIData}
          className="mt-3 text-sm text-blue-600 hover:text-blue-800"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">AI Analyzed</p>
              <p className="text-2xl font-bold text-gray-900">
                {aiInsights?.aiAnalyzed || 0}
              </p>
              <p className="text-xs text-gray-500">
                of {aiInsights?.totalThreats || 0} total threats
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Shield className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Confidence</p>
              <p className="text-2xl font-bold text-gray-900">
                {aiInsights?.highConfidence || 0}
              </p>
              <p className="text-xs text-gray-500">
                AI analysis results
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Critical Threats</p>
              <p className="text-2xl font-bold text-gray-900">
                {aiInsights?.criticalThreats || 0}
              </p>
              <p className="text-xs text-gray-500">
                Require immediate attention
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Zap className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Auto Responses</p>
              <p className="text-2xl font-bold text-gray-900">
                {aiInsights?.automatedResponses || 0}
              </p>
              <p className="text-xs text-gray-500">
                Automated actions taken
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Active Campaigns */}
      {threatCorrelations?.activeCampaigns && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Active Attack Campaigns</h3>
            <span className="text-sm text-gray-500">
              {threatCorrelations.activeCampaigns.length} campaigns detected
            </span>
          </div>
          
          <div className="space-y-4">
            {threatCorrelations.activeCampaigns.map((campaign) => (
              <div key={campaign.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{campaign.name}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getCampaignStatusColor(campaign.status)}`}>
                    {campaign.status}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Threats:</span>
                    <span className="ml-1 font-medium">{campaign.threatCount}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Confidence:</span>
                    <span className="ml-1 font-medium">{campaign.confidence}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Last Seen:</span>
                    <span className="ml-1 font-medium">{campaign.lastSeen}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Threat Distribution */}
      {threatCorrelations?.topThreats && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Threat Distribution</h3>
          
          <div className="space-y-3">
            {threatCorrelations.topThreats.map((threat, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                  <span className="text-sm font-medium text-gray-900">{threat.type}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">{threat.count} threats</span>
                  {getTrendIcon(threat.trend)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MCP Server Status */}
      {mcpStatus && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">MCP Server Status</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(mcpStatus).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Target className="h-4 w-4 text-blue-600 mr-2" />
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {name.replace('_', ' ')}
                  </span>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  status.status === 'online' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {status.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Recommendations */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Recommendations</h3>
        
        <div className="space-y-3">
          <div className="flex items-start">
            <div className="p-1 bg-blue-100 rounded-full mr-3 mt-1">
              <Brain className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Enable Automated Response</p>
              <p className="text-sm text-gray-600">
                AI suggests enabling automated responses for high-confidence threats to reduce response time.
              </p>
            </div>
          </div>
          
          <div className="flex items-start">
            <div className="p-1 bg-yellow-100 rounded-full mr-3 mt-1">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Review False Positives</p>
              <p className="text-sm text-gray-600">
                {aiInsights?.falsePositives || 0} false positives detected. Consider adjusting detection rules.
              </p>
            </div>
          </div>
          
          <div className="flex items-start">
            <div className="p-1 bg-green-100 rounded-full mr-3 mt-1">
              <Shield className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Update Threat Intelligence</p>
              <p className="text-sm text-gray-600">
                AI recommends updating threat intelligence feeds for better detection accuracy.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIDashboard;
