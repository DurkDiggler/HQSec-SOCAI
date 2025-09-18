import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Shield,
  Target,
  AlertTriangle,
  Activity,
  TrendingUp,
  Users,
  Database,
  Zap,
} from 'lucide-react';

// Import individual dashboard components
import ThreatHuntingDashboard from './ThreatHuntingDashboard';
import AttackAttributionDashboard from './AttackAttributionDashboard';
import VulnerabilityCorrelationDashboard from './VulnerabilityCorrelationDashboard';
import BusinessImpactDashboard from './BusinessImpactDashboard';
import ThreatIntelligenceDashboard from './ThreatIntelligenceDashboard';
import MCPIntegrationDashboard from './MCPIntegrationDashboard';

const AnalyticsDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/analytics/dashboard/overview');
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getThreatLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Advanced Analytics Dashboard</h1>
        <Button onClick={loadDashboardData} variant="outline" size="sm">
          <Activity className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="threat-hunting">Threat Hunting</TabsTrigger>
          <TabsTrigger value="attack-attribution">Attack Attribution</TabsTrigger>
          <TabsTrigger value="vulnerability">Vulnerability</TabsTrigger>
          <TabsTrigger value="business-impact">Business Impact</TabsTrigger>
          <TabsTrigger value="threat-intelligence">Threat Intel</TabsTrigger>
          <TabsTrigger value="mcp-integration">MCP Tools</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Overview Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Alerts</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData?.threat_landscape?.total_alerts || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Last 24 hours
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">High Severity</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {dashboardData?.threat_landscape?.high_severity_alerts || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Critical & High alerts
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Incidents</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardData?.threat_landscape?.total_incidents || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Active incidents
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Threat Level</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold px-2 py-1 rounded ${getThreatLevelColor(dashboardData?.threat_landscape?.threat_level)}`}>
                  {dashboardData?.threat_landscape?.threat_level || 'Unknown'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Current threat level
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Security Metrics */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Security Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Mean Time to Detection</span>
                  <span className="text-sm text-muted-foreground">
                    {dashboardData?.security_metrics?.mean_time_to_detection || 0} min
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Mean Time to Response</span>
                  <span className="text-sm text-muted-foreground">
                    {dashboardData?.security_metrics?.mean_time_to_response || 0} min
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">False Positive Rate</span>
                  <span className="text-sm text-muted-foreground">
                    {Math.round((dashboardData?.security_metrics?.false_positive_rate || 0) * 100)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Detection Accuracy</span>
                  <span className="text-sm text-muted-foreground">
                    {Math.round((dashboardData?.security_metrics?.threat_detection_accuracy || 0) * 100)}%
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Threats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {dashboardData?.threat_landscape?.top_threats?.map((threat, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{threat[0]}</span>
                      <Badge variant="secondary">{threat[1]}</Badge>
                    </div>
                  )) || (
                    <p className="text-sm text-muted-foreground">No threat data available</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Component Status */}
          <Card>
            <CardHeader>
              <CardTitle>Component Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Threat Hunting</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Attack Attribution</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Vulnerability Analysis</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Business Impact</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Threat Intelligence</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">MCP Integration</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recommendations */}
          {dashboardData?.recommendations && dashboardData.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {dashboardData.recommendations.map((rec, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                      <p className="text-sm">{rec}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="threat-hunting">
          <ThreatHuntingDashboard />
        </TabsContent>

        <TabsContent value="attack-attribution">
          <AttackAttributionDashboard />
        </TabsContent>

        <TabsContent value="vulnerability">
          <VulnerabilityCorrelationDashboard />
        </TabsContent>

        <TabsContent value="business-impact">
          <BusinessImpactDashboard />
        </TabsContent>

        <TabsContent value="threat-intelligence">
          <ThreatIntelligenceDashboard />
        </TabsContent>

        <TabsContent value="mcp-integration">
          <MCPIntegrationDashboard />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;
