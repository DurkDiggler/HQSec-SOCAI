import React from 'react';
import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { clsx } from 'clsx';
import type { ChartData } from '../../types';

interface PieChartProps {
  data: ChartData[];
  title?: string;
  height?: number;
  className?: string;
  colors?: string[];
  showLegend?: boolean;
  showLabel?: boolean;
  innerRadius?: number;
  outerRadius?: number;
  dataKey?: string;
  nameKey?: string;
}

const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  height = 300,
  className,
  colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316', '#06B6D4', '#84CC16'],
  showLegend = true,
  showLabel = false,
  innerRadius = 0,
  outerRadius = 80,
  dataKey = 'value',
  nameKey = 'name',
}) => {
  const formatTooltipLabel = (label: any, payload: any) => {
    if (payload && payload.length > 0) {
      const total = payload.reduce((sum: number, item: any) => sum + item.value, 0);
      const percentage = ((payload[0].value / total) * 100).toFixed(1);
      return `${label}: ${percentage}%`;
    }
    return label;
  };

  const formatTooltipValue = (value: any) => {
    return [value, 'Count'];
  };

  return (
    <div className={clsx('w-full', className)}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      
      <ResponsiveContainer width="100%" height={height}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            dataKey={dataKey}
            nameKey={nameKey}
            label={showLabel}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || colors[index % colors.length]}
              />
            ))}
          </Pie>
          
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
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PieChart;
