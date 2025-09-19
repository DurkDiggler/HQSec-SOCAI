import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from './index';
import type {
  Alert,
  AlertFilters,
  Statistics,
  User,
  AIAnalysis,
  MCPScanResult,
  Settings,
  ApiResponse,
  PaginatedResponse,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost/api/v1';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Alert', 'Statistics', 'User', 'AIAnalysis', 'MCPScan', 'Settings'],
  endpoints: (builder) => ({
    // Authentication endpoints
    login: builder.mutation<
      ApiResponse<{ user: User; access_token: string; refresh_token: string }>,
      { email: string; password: string }
    >({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
      invalidatesTags: ['User'],
    }),

    register: builder.mutation<
      ApiResponse<{ user: User; access_token: string; refresh_token: string }>,
      {
        username: string;
        email: string;
        password: string;
        first_name?: string;
        last_name?: string;
      }
    >({
      query: (userData) => ({
        url: '/auth/register',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),

    refreshToken: builder.mutation<
      ApiResponse<{ access_token: string; refresh_token: string }>,
      { refresh_token: string }
    >({
      query: ({ refresh_token }) => ({
        url: '/auth/refresh',
        method: 'POST',
        body: { refresh_token },
      }),
    }),

    logout: builder.mutation<ApiResponse, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),

    getCurrentUser: builder.query<ApiResponse<User>, void>({
      query: () => '/auth/me',
      providesTags: ['User'],
    }),

    // Alerts endpoints
    getAlerts: builder.query<PaginatedResponse<Alert>, AlertFilters>({
      query: (params) => ({
        url: '/alerts',
        params,
      }),
      providesTags: ['Alert'],
    }),

    getAlert: builder.query<ApiResponse<Alert>, number>({
      query: (id) => `/alerts/${id}`,
      providesTags: (result, error, id) => [{ type: 'Alert', id }],
    }),

    updateAlertStatus: builder.mutation<
      ApiResponse<Alert>,
      { id: number; status: string; assigned_to?: string; notes?: string }
    >({
      query: ({ id, ...updates }) => ({
        url: `/alerts/${id}/status`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Alert', id },
        'Alert',
      ],
    }),

    getAlertIOCs: builder.query<ApiResponse<any>, number>({
      query: (id) => `/alerts/${id}/iocs`,
    }),

    // Statistics endpoints
    getStatistics: builder.query<ApiResponse<Statistics>, { days?: number }>({
      query: (params) => ({
        url: '/statistics',
        params,
      }),
      providesTags: ['Statistics'],
    }),

    getDashboardData: builder.query<ApiResponse<any>, { days?: number }>({
      query: (params) => ({
        url: '/dashboard',
        params,
      }),
      providesTags: ['Statistics'],
    }),

    getTopSources: builder.query<ApiResponse<any[]>, { limit?: number }>({
      query: (params) => ({
        url: '/statistics/sources',
        params,
      }),
    }),

    getTopEventTypes: builder.query<ApiResponse<any[]>, { limit?: number }>({
      query: (params) => ({
        url: '/statistics/event-types',
        params,
      }),
    }),

    getTopIPs: builder.query<ApiResponse<any[]>, { limit?: number }>({
      query: (params) => ({
        url: '/statistics/ips',
        params,
      }),
    }),

    getFilters: builder.query<ApiResponse<any>, void>({
      query: () => '/filters',
    }),

    // AI Analysis endpoints
    analyzeAlert: builder.mutation<ApiResponse<AIAnalysis>, number>({
      query: (alertId) => ({
        url: `/ai/analyze/${alertId}`,
        method: 'POST',
      }),
      invalidatesTags: ['AIAnalysis'],
    }),

    assessRisk: builder.mutation<ApiResponse<any>, any>({
      query: (threatData) => ({
        url: '/ai/risk-assessment',
        method: 'POST',
        body: threatData,
      }),
    }),

    correlateThreats: builder.mutation<ApiResponse<any>, number[]>({
      query: (eventIds) => ({
        url: '/ai/correlate-threats',
        method: 'POST',
        body: eventIds,
      }),
    }),

    // MCP Server endpoints
    scanTarget: builder.mutation<ApiResponse<MCPScanResult>, { target: string; scan_type?: string }>({
      query: ({ target, scan_type = 'basic' }) => ({
        url: '/mcp/scan',
        method: 'POST',
        params: { target, scan_type },
      }),
      invalidatesTags: ['MCPScan'],
    }),

    testExploit: builder.mutation<ApiResponse<any>, { target: string; vulnerability: string; exploit_type?: string }>({
      query: ({ target, vulnerability, exploit_type = 'basic' }) => ({
        url: '/mcp/test-exploit',
        method: 'POST',
        params: { target, vulnerability, exploit_type },
      }),
    }),

    getMCPStatus: builder.query<ApiResponse<any>, void>({
      query: () => '/mcp/status',
      providesTags: ['MCPScan'],
    }),

    getMCPCapabilities: builder.query<ApiResponse<any>, void>({
      query: () => '/mcp/capabilities',
    }),

    // Settings endpoints
    getSettings: builder.query<ApiResponse<Settings>, void>({
      query: () => '/settings',
      providesTags: ['Settings'],
    }),

    testEmail: builder.mutation<ApiResponse<any>, void>({
      query: () => ({
        url: '/settings/test-email',
        method: 'POST',
      }),
    }),

    testIntel: builder.mutation<ApiResponse<any>, void>({
      query: () => ({
        url: '/settings/test-intel',
        method: 'POST',
      }),
    }),

    testDatabase: builder.mutation<ApiResponse<any>, void>({
      query: () => ({
        url: '/settings/test-database',
        method: 'POST',
      }),
    }),

    // Health check
    healthCheck: builder.query<ApiResponse<any>, void>({
      query: () => '/health',
    }),
  }),
});

export const {
  // Authentication
  useLoginMutation,
  useRegisterMutation,
  useRefreshTokenMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
  
  // Alerts
  useGetAlertsQuery,
  useGetAlertQuery,
  useUpdateAlertStatusMutation,
  useGetAlertIOCsQuery,
  
  // Statistics
  useGetStatisticsQuery,
  useGetDashboardDataQuery,
  useGetTopSourcesQuery,
  useGetTopEventTypesQuery,
  useGetTopIPsQuery,
  useGetFiltersQuery,
  
  // AI Analysis
  useAnalyzeAlertMutation,
  useAssessRiskMutation,
  useCorrelateThreatsMutation,
  
  // MCP Servers
  useScanTargetMutation,
  useTestExploitMutation,
  useGetMCPStatusQuery,
  useGetMCPCapabilitiesQuery,
  
  // Settings
  useGetSettingsQuery,
  useTestEmailMutation,
  useTestIntelMutation,
  useTestDatabaseMutation,
  
  // Health
  useHealthCheckQuery,
} = api;
