import React from 'react';
import { Wifi, WifiOff, AlertCircle, CheckCircle } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { Button } from './ui/Button';
import clsx from 'clsx';

interface ConnectionStatusProps {
  showDetails?: boolean;
  className?: string;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  showDetails = false,
  className,
}) => {
  const { isConnected, connectionState, connect, disconnect, error } = useWebSocket();

  const getStatusInfo = () => {
    if (isConnected) {
      return {
        icon: <CheckCircle className="h-4 w-4 text-green-500" />,
        text: 'Connected',
        color: 'text-green-600 dark:text-green-400',
        bgColor: 'bg-green-100 dark:bg-green-900/20',
        borderColor: 'border-green-200 dark:border-green-800',
      };
    }

    if (error) {
      return {
        icon: <AlertCircle className="h-4 w-4 text-red-500" />,
        text: 'Error',
        color: 'text-red-600 dark:text-red-400',
        bgColor: 'bg-red-100 dark:bg-red-900/20',
        borderColor: 'border-red-200 dark:border-red-800',
      };
    }

    return {
      icon: <WifiOff className="h-4 w-4 text-yellow-500" />,
      text: 'Disconnected',
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
      borderColor: 'border-yellow-200 dark:border-yellow-800',
    };
  };

  const statusInfo = getStatusInfo();

  const getConnectionStateText = () => {
    switch (connectionState) {
      case WebSocket.CONNECTING:
        return 'Connecting...';
      case WebSocket.OPEN:
        return 'Connected';
      case WebSocket.CLOSING:
        return 'Disconnecting...';
      case WebSocket.CLOSED:
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  if (showDetails) {
    return (
      <div className={clsx(
        'p-3 rounded-lg border',
        statusInfo.bgColor,
        statusInfo.borderColor,
        className
      )}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {statusInfo.icon}
            <div>
              <p className={clsx('text-sm font-medium', statusInfo.color)}>
                {statusInfo.text}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {getConnectionStateText()}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Button
                size="sm"
                variant="secondary"
                onClick={disconnect}
              >
                Disconnect
              </Button>
            ) : (
              <Button
                size="sm"
                variant="primary"
                onClick={connect}
              >
                Connect
              </Button>
            )}
          </div>
        </div>
        
        {error && (
          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs text-red-600 dark:text-red-400">
            {error}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={clsx('flex items-center space-x-2', className)}>
      <div className="flex items-center space-x-1">
        {isConnected ? (
          <Wifi className="h-4 w-4 text-green-500" />
        ) : (
          <WifiOff className="h-4 w-4 text-yellow-500" />
        )}
        <span className={clsx('text-sm', statusInfo.color)}>
          {isConnected ? 'Live' : 'Offline'}
        </span>
      </div>
      
      {!isConnected && (
        <button
          onClick={connect}
          className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
        >
          Reconnect
        </button>
      )}
    </div>
  );
};

export default ConnectionStatus;
