import React from 'react';
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { clsx } from 'clsx';
import type { ChartData } from '../../types';

interface BarChartProps {
  data: ChartData[];
  title?: string;
  height?: number;
  className?: string;
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  xAxisKey?: string;
  yAxisKey?: string;
  bars?: Array<{
    dataKey: string;
    name: string;
    color?: string;
  }>;
  orientation?: 'vertical' | 'horizontal';
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  title,
  height = 300,
  className,
  colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
  showLegend = true,
  showGrid = true,
  xAxisKey = 'name',
  yAxisKey = 'value',
  bars = [{ dataKey: 'value', name: 'Value' }],
  orientation = 'vertical',
}) => {
  const formatTooltipLabel = (label: any) => {
    return label;
  };

  const formatTooltipValue = (value: any, name: string) => {
    return [value, name];
  };

  return (
    <div className={clsx('w-full', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
          layout={orientation === 'horizontal' ? 'horizontal' : 'vertical'}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
          
          <XAxis
            dataKey={orientation === 'horizontal' ? yAxisKey : xAxisKey}
            stroke="#6B7280"
            fontSize={12}
            type={orientation === 'horizontal' ? 'number' : 'category'}
          />
          
          <YAxis
            dataKey={orientation === 'horizontal' ? xAxisKey : yAxisKey}
            stroke="#6B7280"
            fontSize={12}
            type={orientation === 'horizontal' ? 'category' : 'number'}
          />
          
          <Tooltip
            labelFormatter={formatTooltipLabel}
            formatter={formatTooltipValue}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
          
          {showLegend && <Legend />}
          
          {bars.map((bar, index) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              name={bar.name}
              fill={bar.color || colors[index % colors.length]}
              radius={[2, 2, 0, 0]}
            />
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BarChart;
