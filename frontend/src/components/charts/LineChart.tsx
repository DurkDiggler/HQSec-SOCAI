import React from 'react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { clsx } from 'clsx';
import type { TimeSeriesData } from '../../types';

interface LineChartProps {
  data: TimeSeriesData[];
  title?: string;
  height?: number;
  className?: string;
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  xAxisKey?: string;
  yAxisKey?: string;
  lines?: Array<{
    dataKey: string;
    name: string;
    color?: string;
    strokeWidth?: number;
  }>;
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  title,
  height = 300,
  className,
  colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
  showLegend = true,
  showGrid = true,
  xAxisKey = 'timestamp',
  yAxisKey = 'value',
  lines = [{ dataKey: 'value', name: 'Value' }],
}) => {
  const formatXAxisTick = (tickItem: any) => {
    if (xAxisKey === 'timestamp') {
      return new Date(tickItem).toLocaleDateString();
    }
    return tickItem;
  };

  const formatTooltipLabel = (label: any) => {
    if (xAxisKey === 'timestamp') {
      return new Date(label).toLocaleString();
    }
    return label;
  };

  return (
    <div className={clsx('w-full', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
          
          <XAxis
            dataKey={xAxisKey}
            tickFormatter={formatXAxisTick}
            stroke="#6B7280"
            fontSize={12}
          />
          
          <YAxis
            dataKey={yAxisKey}
            stroke="#6B7280"
            fontSize={12}
          />
          
          <Tooltip
            labelFormatter={formatTooltipLabel}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
          />
          
          {showLegend && <Legend />}
          
          {lines.map((line, index) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color || colors[index % colors.length]}
              strokeWidth={line.strokeWidth || 2}
              dot={{ fill: line.color || colors[index % colors.length], strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, strokeWidth: 2 }}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LineChart;
