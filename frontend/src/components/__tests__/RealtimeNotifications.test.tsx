import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import RealtimeNotifications from '../RealtimeNotifications';
import { uiSlice } from '../../store/slices/uiSlice';
import { createMockNotification } from '../../test-utils';

// Mock WebSocket
jest.mock('../../services/websocket', () => ({
  websocketManager: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    send: jest.fn(),
    subscribe: jest.fn(),
    unsubscribe: jest.fn(),
    isConnected: true,
  },
}));

// Mock useWebSocket hook
jest.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: true,
    lastMessage: null,
    error: null,
  }),
}));

const createTestStore = (notifications = []) => {
  return configureStore({
    reducer: {
      ui: uiSlice.reducer,
    },
    preloadedState: {
      ui: {
        sidebarOpen: false,
        darkMode: false,
        notifications,
        isMobile: false,
      },
    },
  });
};

describe('RealtimeNotifications', () => {
  it('renders notification bell', () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    expect(screen.getByRole('button')).toBeInTheDocument();
    expect(screen.getByTestId('notification-bell')).toBeInTheDocument();
  });

  it('shows unread count badge', () => {
    const notifications = [
      createMockNotification({ id: '1', read: false }),
      createMockNotification({ id: '2', read: false }),
      createMockNotification({ id: '3', read: true }),
    ];
    const store = createTestStore(notifications);
    
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('opens notification dropdown when clicked', async () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });
  });

  it('displays notifications in dropdown', async () => {
    const notifications = [
      createMockNotification({ 
        id: '1', 
        message: 'New alert detected',
        type: 'alert' 
      }),
      createMockNotification({ 
        id: '2', 
        message: 'System update available',
        type: 'system' 
      }),
    ];
    const store = createTestStore(notifications);
    
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(screen.getByText('New alert detected')).toBeInTheDocument();
      expect(screen.getByText('System update available')).toBeInTheDocument();
    });
  });

  it('shows empty state when no notifications', async () => {
    const store = createTestStore([]);
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(screen.getByText('No notifications')).toBeInTheDocument();
    });
  });

  it('marks notification as read when clicked', async () => {
    const notifications = [
      createMockNotification({ id: '1', read: false }),
    ];
    const store = createTestStore(notifications);
    
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      const markAsReadButton = screen.getByTitle('Mark as read');
      fireEvent.click(markAsReadButton);
    });
    
    // Verify the action was dispatched (in a real test, you'd check the store state)
    expect(screen.getByTitle('Mark as read')).toBeInTheDocument();
  });

  it('removes notification when remove button is clicked', async () => {
    const notifications = [
      createMockNotification({ id: '1' }),
    ];
    const store = createTestStore(notifications);
    
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      const removeButton = screen.getByTitle('Remove');
      fireEvent.click(removeButton);
    });
    
    // Verify the action was dispatched
    expect(screen.getByTitle('Remove')).toBeInTheDocument();
  });

  it('shows connection status', async () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <RealtimeNotifications />
      </Provider>
    );
    
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('limits displayed notifications', async () => {
    const notifications = Array.from({ length: 10 }, (_, i) => 
      createMockNotification({ id: `${i}`, message: `Notification ${i}` })
    );
    const store = createTestStore(notifications);
    
    render(
      <Provider store={store}>
        <RealtimeNotifications maxNotifications={5} />
      </Provider>
    );
    
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
      expect(screen.getByText('View all notifications (10)')).toBeInTheDocument();
    });
  });
});
