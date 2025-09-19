import { setupServer } from 'msw/node';
import { rest } from 'msw';
import type { Alert, User, PaginatedResponse } from '../types';

// Mock data
const mockUser: User = {
  id: '1',
  email: 'admin@socagent.com',
  username: 'admin',
  roles: ['admin'],
  permissions: ['*'],
  is_active: true,
  mfa_enabled: false,
};

const mockAlerts: Alert[] = [
  {
    id: 1,
    source: 'Firewall',
    event_type: 'Blocked Connection',
    severity: 8,
    timestamp: new Date().toISOString(),
    message: 'Blocked suspicious connection attempt',
    ip: '192.168.1.100',
    username: 'user1',
    status: 'new',
    assigned_to: null,
    threat_score: 8.5,
    category: 'Network',
    raw_data: {},
    ioc_data: {},
  },
  {
    id: 2,
    source: 'IDS',
    event_type: 'Intrusion Attempt',
    severity: 6,
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    message: 'Potential intrusion detected',
    ip: '10.0.0.50',
    username: null,
    status: 'investigating',
    assigned_to: 'analyst1',
    threat_score: 6.2,
    category: 'Security',
    raw_data: {},
    ioc_data: {},
  },
];

const mockStatistics = {
  total_alerts: 1250,
  high_severity: 45,
  resolved_alerts: 1200,
  false_positives: 25,
  avg_response_time: 2.1,
};

// Mock handlers
const handlers = [
  // Auth endpoints
  rest.post('/api/v1/auth/login', (req, res, ctx) => {
    return res(
      ctx.json({
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
      })
    );
  }),

  rest.post('/api/v1/auth/refresh', (req, res, ctx) => {
    return res(
      ctx.json({
        access_token: 'new-mock-access-token',
        refresh_token: 'new-mock-refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
      })
    );
  }),

  rest.get('/api/v1/auth/me', (req, res, ctx) => {
    return res(ctx.json(mockUser));
  }),

  // Alerts endpoints
  rest.get('/api/v1/alerts', (req, res, ctx) => {
    const url = new URL(req.url);
    const skip = parseInt(url.searchParams.get('skip') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '50');
    const status = url.searchParams.get('status');
    const severity = url.searchParams.get('severity');

    let filteredAlerts = [...mockAlerts];

    if (status) {
      filteredAlerts = filteredAlerts.filter(alert => alert.status === status);
    }

    if (severity) {
      const severityNum = parseInt(severity);
      filteredAlerts = filteredAlerts.filter(alert => alert.severity >= severityNum);
    }

    const paginatedResponse: PaginatedResponse<Alert> = {
      data: filteredAlerts.slice(skip, skip + limit),
      pagination: {
        skip,
        limit,
        total: filteredAlerts.length,
        has_more: skip + limit < filteredAlerts.length,
      },
    };

    return res(ctx.json(paginatedResponse));
  }),

  rest.get('/api/v1/alerts/:id', (req, res, ctx) => {
    const { id } = req.params;
    const alert = mockAlerts.find(a => a.id === parseInt(id as string));
    
    if (!alert) {
      return res(ctx.status(404), ctx.json({ message: 'Alert not found' }));
    }

    return res(ctx.json({ data: alert }));
  }),

  rest.patch('/api/v1/alerts/:id/status', (req, res, ctx) => {
    const { id } = req.params;
    const alert = mockAlerts.find(a => a.id === parseInt(id as string));
    
    if (!alert) {
      return res(ctx.status(404), ctx.json({ message: 'Alert not found' }));
    }

    // Update alert status
    alert.status = 'investigating';
    alert.assigned_to = 'analyst1';

    return res(ctx.json({ data: alert }));
  }),

  // Statistics endpoints
  rest.get('/api/v1/statistics', (req, res, ctx) => {
    return res(ctx.json({ data: mockStatistics }));
  }),

  // Dashboard endpoints
  rest.get('/api/v1/dashboard', (req, res, ctx) => {
    return res(ctx.json({
      data: {
        recent_alerts: mockAlerts.slice(0, 5),
        system_health: {
          status: 'healthy',
          uptime: '99.9%',
          response_time: '2.1s',
        },
        metrics: mockStatistics,
      },
    }));
  }),

  // Settings endpoints
  rest.get('/api/v1/settings', (req, res, ctx) => {
    return res(ctx.json({
      data: {
        app_host: '0.0.0.0',
        app_port: 8000,
        log_level: 'INFO',
        oauth_enabled: true,
        mfa_enabled: true,
        rbac_enabled: true,
        ml_enabled: true,
        rate_limit_requests: 100,
        rate_limit_window: 3600,
      },
    }));
  }),

  // Test endpoints
  rest.post('/api/v1/test/email', (req, res, ctx) => {
    return res(ctx.json({ message: 'Email test successful' }));
  }),

  rest.post('/api/v1/test/database', (req, res, ctx) => {
    return res(ctx.json({ message: 'Database test successful' }));
  }),

  rest.post('/api/v1/test/intel', (req, res, ctx) => {
    return res(ctx.json({ message: 'Intel test successful' }));
  }),

  // Catch-all handler for unhandled requests
  rest.get('*', (req, res, ctx) => {
    console.warn(`Unhandled GET request: ${req.url}`);
    return res(ctx.status(404), ctx.json({ message: 'Not found' }));
  }),

  rest.post('*', (req, res, ctx) => {
    console.warn(`Unhandled POST request: ${req.url}`);
    return res(ctx.status(404), ctx.json({ message: 'Not found' }));
  }),
];

// Create the mock server
export const server = setupServer(...handlers);
