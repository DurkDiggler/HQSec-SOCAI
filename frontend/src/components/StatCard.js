import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color, change, changeType }) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    red: 'text-red-600 bg-red-50',
    yellow: 'text-yellow-600 bg-yellow-50',
    green: 'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50',
  };

  const changeColorClasses = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
        
        {change && (
          <div className="mt-4 flex items-center">
            {changeType === 'positive' ? (
              <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
            ) : changeType === 'negative' ? (
              <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
            ) : (
              <div className="h-4 w-4 mr-1" />
            )}
            <span className={`text-sm font-medium ${changeColorClasses[changeType]}`}>
              {change}
            </span>
            <span className="text-sm text-gray-500 ml-1">from last period</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
