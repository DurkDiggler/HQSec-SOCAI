import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { configureStore } from '@reduxjs/toolkit';
import { store } from './store';
import type { RootState } from './store';

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <HelmetProvider>
          <BrowserRouter>
            {children}
          </BrowserRouter>
        </HelmetProvider>
      </QueryClientProvider>
    </Provider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Create a test store with custom state
export const createTestStore = (preloadedState?: Partial<RootState>) => {
  return configureStore({
    reducer: store.getState,
    preloadedState,
  });
};

// Mock WebSocket for testing
export const mockWebSocket = {
  readyState: WebSocket.OPEN,
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
};

// Mock WebSocket manager
export const mockWebSocketManager = {
  connect: jest.fn().mockResolvedValue(undefined),
  disconnect: jest.fn(),
  send: jest.fn(),
  subscribe: jest.fn(),
  unsubscribe: jest.fn(),
  isConnected: true,
  connectionState: WebSocket.OPEN,
};

// Test data factories
export const createMockAlert = (overrides: Partial<Alert> = {}): Alert => ({
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
  ...overrides,
});

export const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: '1',
  email: 'admin@socagent.com',
  username: 'admin',
  roles: ['admin'],
  permissions: ['*'],
  is_active: true,
  mfa_enabled: false,
  ...overrides,
});

export const createMockNotification = (overrides: Partial<Notification> = {}): Notification => ({
  id: '1',
  type: 'alert',
  message: 'New high severity alert',
  timestamp: new Date().toISOString(),
  read: false,
  link: '/alerts/1',
  ...overrides,
});

// Helper functions
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0));
};

export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.IntersectionObserver = mockIntersectionObserver;
};

export const mockResizeObserver = () => {
  const mockResizeObserver = jest.fn();
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.ResizeObserver = mockResizeObserver;
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };
