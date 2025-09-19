import React from 'react';
import { render, screen, waitFor } from '../../test-utils';
import Dashboard from '../Dashboard';

// Mock the API hooks
jest.mock('../../store/api', () => ({
  useGetDashboardDataQuery: () => ({
    data: {
      data: {
        recent_alerts: [],
        system_health: {
          status: 'healthy',
          uptime: '99.9%',
          response_time: '2.1s',
        },
        metrics: {
          total_alerts: 1250,
          high_severity: 45,
          resolved_alerts: 1200,
          false_positives: 25,
        },
      },
    },
    isLoading: false,
    error: null,
  }),
  useGetStatisticsQuery: () => ({
    data: {
      data: {
        total_alerts: 1250,
        high_severity: 45,
        resolved_alerts: 1200,
        false_positives: 25,
        avg_response_time: 2.1,
      },
    },
    isLoading: false,
    error: null,
  }),
}));

// Mock the RealtimeMetrics component
jest.mock('../../components/RealtimeMetrics', () => {
  return function MockRealtimeMetrics() {
    return <div data-testid="realtime-metrics">Real-time Metrics</div>;
  };
});

describe('Dashboard', () => {
  it('renders dashboard title and description', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Overview of your security posture and recent activity')).toBeInTheDocument();
  });

  it('renders statistics cards', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Total Alerts')).toBeInTheDocument();
    expect(screen.getByText('1,250')).toBeInTheDocument();
    
    expect(screen.getByText('High Severity')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();
    
    expect(screen.getByText('Resolved')).toBeInTheDocument();
    expect(screen.getByText('1,200')).toBeInTheDocument();
    
    expect(screen.getByText('False Positives')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  it('renders real-time metrics component', () => {
    render(<Dashboard />);
    
    expect(screen.getByTestId('realtime-metrics')).toBeInTheDocument();
  });

  it('renders charts section', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Alert Trends (7 days)')).toBeInTheDocument();
    expect(screen.getByText('Severity Distribution')).toBeInTheDocument();
    expect(screen.getByText('Top Alert Sources')).toBeInTheDocument();
  });

  it('shows loading state when data is loading', () => {
    // Mock loading state
    jest.doMock('../../store/api', () => ({
      useGetDashboardDataQuery: () => ({
        data: null,
        isLoading: true,
        error: null,
      }),
      useGetStatisticsQuery: () => ({
        data: null,
        isLoading: true,
        error: null,
      }),
    }));

    render(<Dashboard />);
    
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('shows error state when data fails to load', () => {
    // Mock error state
    jest.doMock('../../store/api', () => ({
      useGetDashboardDataQuery: () => ({
        data: null,
        isLoading: false,
        error: { message: 'Failed to load dashboard data' },
      }),
      useGetStatisticsQuery: () => ({
        data: null,
        isLoading: false,
        error: { message: 'Failed to load statistics' },
      }),
    }));

    render(<Dashboard />);
    
    expect(screen.getByText('Error loading dashboard')).toBeInTheDocument();
    expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
  });

  it('displays percentage changes for statistics', () => {
    render(<Dashboard />);
    
    // Check for percentage changes
    expect(screen.getByText('+12%')).toBeInTheDocument();
    expect(screen.getByText('+8%')).toBeInTheDocument();
    expect(screen.getByText('+15%')).toBeInTheDocument();
    expect(screen.getByText('-5%')).toBeInTheDocument();
  });

  it('renders with proper accessibility attributes', () => {
    render(<Dashboard />);
    
    // Check for proper heading structure
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Security Dashboard');
    
    // Check for proper button roles
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});
