import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { Alert, AlertFilters, Severity } from '../../types';

interface AlertsState {
  filters: AlertFilters;
  selectedAlerts: number[];
  sortField: string;
  sortOrder: 'asc' | 'desc';
  viewMode: 'table' | 'grid' | 'timeline';
  realtimeAlerts: Alert[];
  isRealtimeEnabled: boolean;
}

const initialState: AlertsState = {
  filters: {
    skip: 0,
    limit: 50,
  },
  selectedAlerts: [],
  sortField: 'timestamp',
  sortOrder: 'desc',
  viewMode: 'table',
  realtimeAlerts: [],
  isRealtimeEnabled: false,
};

const alertsSlice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<Partial<AlertFilters>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    resetFilters: (state) => {
      state.filters = {
        skip: 0,
        limit: 50,
      };
    },
    setSelectedAlerts: (state, action: PayloadAction<number[]>) => {
      state.selectedAlerts = action.payload;
    },
    toggleAlertSelection: (state, action: PayloadAction<number>) => {
      const alertId = action.payload;
      const index = state.selectedAlerts.indexOf(alertId);
      if (index > -1) {
        state.selectedAlerts.splice(index, 1);
      } else {
        state.selectedAlerts.push(alertId);
      }
    },
    clearSelection: (state) => {
      state.selectedAlerts = [];
    },
    setSorting: (state, action: PayloadAction<{ field: string; order: 'asc' | 'desc' }>) => {
      state.sortField = action.payload.field;
      state.sortOrder = action.payload.order;
    },
    setViewMode: (state, action: PayloadAction<'table' | 'grid' | 'timeline'>) => {
      state.viewMode = action.payload;
    },
    addRealtimeAlert: (state, action: PayloadAction<Alert>) => {
      state.realtimeAlerts.unshift(action.payload);
      // Keep only last 100 realtime alerts
      if (state.realtimeAlerts.length > 100) {
        state.realtimeAlerts = state.realtimeAlerts.slice(0, 100);
      }
    },
    clearRealtimeAlerts: (state) => {
      state.realtimeAlerts = [];
    },
    setRealtimeEnabled: (state, action: PayloadAction<boolean>) => {
      state.isRealtimeEnabled = action.payload;
    },
  },
});

export const {
  setFilters,
  resetFilters,
  setSelectedAlerts,
  toggleAlertSelection,
  clearSelection,
  setSorting,
  setViewMode,
  addRealtimeAlert,
  clearRealtimeAlerts,
  setRealtimeEnabled,
} = alertsSlice.actions;

export default alertsSlice.reducer;
