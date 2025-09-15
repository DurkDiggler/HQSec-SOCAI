import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Alerts API
export const alertsAPI = {
  // Get alerts with filtering and pagination
  getAlerts: async (params = {}) => {
    const response = await api.get('/alerts', { params });
    return response.data;
  },

  // Get a specific alert by ID
  getAlert: async (id) => {
    const response = await api.get(`/alerts/${id}`);
    return response.data;
  },

  // Update alert status
  updateAlertStatus: async (id, status, assignedTo = null, notes = null) => {
    const response = await api.patch(`/alerts/${id}/status`, null, {
      params: { status, assigned_to: assignedTo, notes }
    });
    return response.data;
  },

  // Get alert IOCs
  getAlertIOCs: async (id) => {
    const response = await api.get(`/alerts/${id}/iocs`);
    return response.data;
  },
};

// Statistics API
export const statisticsAPI = {
  // Get dashboard statistics
  getStatistics: async (days = 7) => {
    const response = await api.get('/statistics', { params: { days } });
    return response.data;
  },

  // Get top sources
  getTopSources: async (limit = 10) => {
    const response = await api.get('/statistics/sources', { params: { limit } });
    return response.data;
  },

  // Get top event types
  getTopEventTypes: async (limit = 10) => {
    const response = await api.get('/statistics/event-types', { params: { limit } });
    return response.data;
  },

  // Get top IPs
  getTopIPs: async (limit = 10) => {
    const response = await api.get('/statistics/ips', { params: { limit } });
    return response.data;
  },

  // Get comprehensive dashboard data
  getDashboardData: async (days = 7) => {
    const response = await api.get('/dashboard', { params: { days } });
    return response.data;
  },

  // Get available filters
  getFilters: async () => {
    const response = await api.get('/filters');
    return response.data;
  },
};

// Health check API
export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
