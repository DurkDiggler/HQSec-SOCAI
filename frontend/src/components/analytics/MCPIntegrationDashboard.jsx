import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Play,
  Pause,
  RefreshCw,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Target,
  Activity,
  Zap,
} from 'lucide-react';

const MCPIntegrationDashboard = () => {
  const [mcpStatus, setMcpStatus] = useState(null);
  const [availableTools, setAvailableTools] = useState({});
  const [scanHistory, setScanHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [scanForm, setScanForm] = useState({
    target: '',
    scanType: 'comprehensive',
    options: {}
  });
  const [activeScans, setActiveScans] = useState([]);
  const [scanResults, setScanResults] = useState(null);

  useEffect(() => {
    loadMCPStatus();
    loadAvailableTools();
    loadScanHistory();
  }, []);

  const loadMCPStatus = async () => {
    try {
      const response = await fetch('/api/v1/mcp-analytics/tools/status');
      const data = await response.json();
      setMcpStatus(data);
    } catch (error) {
      console.error('Error loading MCP status:', error);
    }
  };

  const loadAvailableTools = async () => {
    try {
      const response = await fetch('/api/v1/mcp-analytics/tools/available');
      const data = await response.json();
      setAvailableTools(data);
    } catch (error) {
      console.error('Error loading available tools:', error);
    }
  };

  const loadScanHistory = async () => {
    try {
      const response = await fetch('/api/v1/mcp-analytics/scan/history');
      const data = await response.json();
      setScanHistory(data);
    } catch (error) {
      console.error('Error loading scan history:', error);
    }
  };

  const runScan = async () => {
    if (!scanForm.target) {
      alert('Please enter a target');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/mcp-analytics/scan/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target: scanForm.target,
          scan_type: scanForm.scanType,
          options: scanForm.options
        }),
      });

      const data = await response.json();
      setScanResults(data);
      
      // Add to active scans
      const newScan = {
        id: Date.now(),
        target: scanForm.target,
        scanType: scanForm.scanType,
        status: data.status,
        startTime: new Date().toISOString(),
        results: data
      };
      setActiveScans(prev => [...prev, newScan]);
      
      // Refresh scan history
      loadScanHistory();
    } catch (error) {
      console.error('Error running scan:', error);
      alert('Error running scan: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const runQuickScan = async () => {
    if (!scanForm.target) {
      alert('Please enter a target');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/mcp-analytics/scan/quick', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target: scanForm.target,
          scan_type: 'nmap'
        }),
      });

      const data = await response.json();
      setScanResults(data);
    } catch (error) {
      console.error('Error running quick scan:', error);
      alert('Error running quick scan: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getSeverityBadge = (severity) => {
    const variants = {
      critical: 'destructive',
      high: 'destructive',
      medium: 'default',
      low: 'secondary',
      info: 'outline'
    };
    return (
      <Badge variant={variants[severity] || 'default'}>
        {severity?.toUpperCase()}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">MCP Security Testing</h2>
        <div className="flex space-x-2">
          <Button
            onClick={loadMCPStatus}
            variant="outline"
            size="sm"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Status
          </Button>
        </div>
      </div>

      {/* MCP Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Kali MCP Server</CardTitle>
            {mcpStatus?.kali_mcp && getStatusIcon(mcpStatus.kali_mcp.status)}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mcpStatus?.kali_mcp?.status || 'Unknown'}
            </div>
            <p className="text-xs text-muted-foreground">
              {mcpStatus?.kali_mcp?.url || 'Not configured'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vulnerability Scanner</CardTitle>
            {mcpStatus?.vuln_scanner && getStatusIcon(mcpStatus.vuln_scanner.status)}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mcpStatus?.vuln_scanner?.status || 'Unknown'}
            </div>
            <p className="text-xs text-muted-foreground">
              {mcpStatus?.vuln_scanner?.url || 'Not configured'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Tools</CardTitle>
            <Shield className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(availableTools).reduce((total, category) => 
                total + Object.keys(availableTools[category] || {}).length, 0
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Security testing tools
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="scan" className="space-y-4">
        <TabsList>
          <TabsTrigger value="scan">Security Scan</TabsTrigger>
          <TabsTrigger value="history">Scan History</TabsTrigger>
          <TabsTrigger value="tools">Available Tools</TabsTrigger>
        </TabsList>

        <TabsContent value="scan" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Run Security Scan</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="target">Target</Label>
                  <Input
                    id="target"
                    placeholder="192.168.1.1 or example.com"
                    value={scanForm.target}
                    onChange={(e) => setScanForm(prev => ({ ...prev, target: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="scanType">Scan Type</Label>
                  <Select
                    value={scanForm.scanType}
                    onValueChange={(value) => setScanForm(prev => ({ ...prev, scanType: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select scan type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="nmap">Nmap Network Scan</SelectItem>
                      <SelectItem value="vuln">Vulnerability Scan</SelectItem>
                      <SelectItem value="web">Web Application Scan</SelectItem>
                      <SelectItem value="network">Network Discovery</SelectItem>
                      <SelectItem value="comprehensive">Comprehensive Scan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={runScan}
                  disabled={isLoading || !scanForm.target}
                  className="flex-1"
                >
                  {isLoading ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Run Scan
                </Button>
                <Button
                  onClick={runQuickScan}
                  disabled={isLoading || !scanForm.target}
                  variant="outline"
                >
                  <Zap className="h-4 w-4 mr-2" />
                  Quick Scan
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Scan Results */}
          {scanResults && (
            <Card>
              <CardHeader>
                <CardTitle>Scan Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {scanResults.findings?.length || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">Total Findings</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">
                        {scanResults.analytics?.high_severity_count || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">High Severity</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {scanResults.analytics?.risk_score ? 
                          Math.round(scanResults.analytics.risk_score * 100) : 0}%
                      </div>
                      <p className="text-sm text-muted-foreground">Risk Score</p>
                    </div>
                  </div>

                  {scanResults.findings && scanResults.findings.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium">Findings</h4>
                      <div className="max-h-96 overflow-y-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Type</TableHead>
                              <TableHead>Target</TableHead>
                              <TableHead>Severity</TableHead>
                              <TableHead>Description</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {scanResults.findings.map((finding, index) => (
                              <TableRow key={index}>
                                <TableCell className="font-medium">
                                  {finding.type}
                                </TableCell>
                                <TableCell>{finding.target}</TableCell>
                                <TableCell>
                                  {getSeverityBadge(finding.severity)}
                                </TableCell>
                                <TableCell className="max-w-xs truncate">
                                  {finding.description}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                  )}

                  {scanResults.recommendations && scanResults.recommendations.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium">Recommendations</h4>
                      <div className="space-y-1">
                        {scanResults.recommendations.map((rec, index) => (
                          <Alert key={index}>
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>{rec}</AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Scan History</CardTitle>
            </CardHeader>
            <CardContent>
              {scanHistory.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Target</TableHead>
                      <TableHead>Scan Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Findings</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {scanHistory.map((scan, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">
                          {scan.target}
                        </TableCell>
                        <TableCell>{scan.scan_type}</TableCell>
                        <TableCell>
                          <Badge variant={scan.status === 'completed' ? 'default' : 'secondary'}>
                            {scan.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{scan.findings?.length || 0}</TableCell>
                        <TableCell>
                          {new Date(scan.start_time).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No scan history available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {Object.entries(availableTools).map(([category, tools]) => (
              <Card key={category}>
                <CardHeader>
                  <CardTitle className="capitalize">{category.replace('_', ' ')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(tools).map(([toolName, toolInfo]) => (
                      <div key={toolName} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">{toolInfo.name}</h4>
                          <Badge variant="outline">Available</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {toolInfo.description}
                        </p>
                        <div className="mt-2">
                          <div className="text-xs text-muted-foreground mb-1">Capabilities:</div>
                          <div className="flex flex-wrap gap-1">
                            {toolInfo.capabilities?.map((capability, index) => (
                              <Badge key={index} variant="secondary" className="text-xs">
                                {capability.replace('_', ' ')}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MCPIntegrationDashboard;
