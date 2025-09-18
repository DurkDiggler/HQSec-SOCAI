import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import InfiniteLoader from 'react-window-infinite-loader';
import { useInView } from 'react-intersection-observer';

/**
 * Virtualized list component for optimal performance with large datasets
 */
const VirtualizedList = ({
  items = [],
  itemHeight = 50,
  height = 400,
  width = '100%',
  onLoadMore,
  hasNextPage = false,
  isLoading = false,
  renderItem,
  className = '',
  style = {},
  threshold = 5,
  ...props
}) => {
  const [loadedItems, setLoadedItems] = useState(new Set());
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const itemCount = hasNextPage ? items.length + 1 : items.length;

  const isItemLoaded = useCallback(
    (index) => {
      return !!items[index] || !hasNextPage;
    },
    [items, hasNextPage]
  );

  const loadMoreItems = useCallback(
    async (startIndex, stopIndex) => {
      if (isLoadingMore || !hasNextPage) return;
      
      setIsLoadingMore(true);
      try {
        await onLoadMore?.(startIndex, stopIndex);
      } finally {
        setIsLoadingMore(false);
      }
    },
    [isLoadingMore, hasNextPage, onLoadMore]
  );

  const Item = useCallback(
    ({ index, style: itemStyle }) => {
      const item = items[index];
      
      if (!item) {
        return (
          <div style={itemStyle} className="virtualized-item-loading">
            <div style={{ padding: '16px', textAlign: 'center' }}>
              {isLoadingMore ? 'Loading...' : 'No more items'}
            </div>
          </div>
        );
      }

      return (
        <div style={itemStyle} className="virtualized-item">
          {renderItem ? renderItem(item, index) : (
            <div style={{ padding: '16px' }}>
              {typeof item === 'string' ? item : JSON.stringify(item)}
            </div>
          )}
        </div>
      );
    },
    [items, isLoadingMore, renderItem]
  );

  return (
    <div className={`virtualized-list ${className}`} style={{ width, ...style }}>
      <InfiniteLoader
        isItemLoaded={isItemLoaded}
        itemCount={itemCount}
        loadMoreItems={loadMoreItems}
        threshold={threshold}
      >
        {({ onItemsRendered, ref }) => (
          <List
            ref={ref}
            height={height}
            itemCount={itemCount}
            itemSize={itemHeight}
            onItemsRendered={onItemsRendered}
            {...props}
          >
            {Item}
          </List>
        )}
      </InfiniteLoader>
    </div>
  );
};

/**
 * Virtualized table component for large datasets
 */
export const VirtualizedTable = ({
  columns = [],
  data = [],
  height = 400,
  rowHeight = 50,
  onLoadMore,
  hasNextPage = false,
  isLoading = false,
  className = '',
  style = {},
  ...props
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [filteredData, setFilteredData] = useState(data);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return filteredData;
    
    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortConfig]);

  const handleSort = useCallback((key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  }, []);

  const Header = useCallback(() => (
    <div className="virtualized-table-header" style={{ display: 'flex', borderBottom: '1px solid #e0e0e0' }}>
      {columns.map((column, index) => (
        <div
          key={column.key || index}
          className="virtualized-table-header-cell"
          style={{
            flex: column.width || 1,
            padding: '12px 16px',
            fontWeight: 'bold',
            cursor: column.sortable ? 'pointer' : 'default',
            backgroundColor: '#f5f5f5',
            borderRight: index < columns.length - 1 ? '1px solid #e0e0e0' : 'none',
          }}
          onClick={() => column.sortable && handleSort(column.key)}
        >
          {column.title}
          {column.sortable && (
            <span style={{ marginLeft: '8px' }}>
              {sortConfig.key === column.key ? (
                sortConfig.direction === 'asc' ? '↑' : '↓'
              ) : '↕'}
            </span>
          )}
        </div>
      ))}
    </div>
  ), [columns, sortConfig, handleSort]);

  const Row = useCallback(({ index, style: rowStyle }) => {
    const item = sortedData[index];
    
    if (!item) {
      return (
        <div style={rowStyle} className="virtualized-table-row-loading">
          <div style={{ padding: '16px', textAlign: 'center' }}>
            {isLoading ? 'Loading...' : 'No more items'}
          </div>
        </div>
      );
    }

    return (
      <div style={rowStyle} className="virtualized-table-row">
        <div style={{ display: 'flex', borderBottom: '1px solid #f0f0f0' }}>
          {columns.map((column, colIndex) => (
            <div
              key={column.key || colIndex}
              className="virtualized-table-cell"
              style={{
                flex: column.width || 1,
                padding: '12px 16px',
                borderRight: colIndex < columns.length - 1 ? '1px solid #f0f0f0' : 'none',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {column.render ? column.render(item[column.key], item, index) : item[column.key]}
            </div>
          ))}
        </div>
      </div>
    );
  }, [sortedData, columns, isLoading]);

  return (
    <div className={`virtualized-table ${className}`} style={{ width: '100%', ...style }}>
      <Header />
      <VirtualizedList
        items={sortedData}
        itemHeight={rowHeight}
        height={height - 50} // Subtract header height
        onLoadMore={onLoadMore}
        hasNextPage={hasNextPage}
        isLoading={isLoading}
        renderItem={Row}
        {...props}
      />
    </div>
  );
};

/**
 * Virtualized grid component for card layouts
 */
export const VirtualizedGrid = ({
  items = [],
  itemHeight = 200,
  itemWidth = 200,
  height = 400,
  onLoadMore,
  hasNextPage = false,
  isLoading = false,
  renderItem,
  className = '',
  style = {},
  ...props
}) => {
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef();

  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  const itemsPerRow = Math.floor(containerWidth / itemWidth) || 1;
  const rowCount = Math.ceil(items.length / itemsPerRow);

  const Row = useCallback(({ index, style: rowStyle }) => {
    const startIndex = index * itemsPerRow;
    const endIndex = Math.min(startIndex + itemsPerRow, items.length);
    const rowItems = items.slice(startIndex, endIndex);

    return (
      <div style={rowStyle} className="virtualized-grid-row">
        <div style={{ display: 'flex', gap: '16px' }}>
          {rowItems.map((item, itemIndex) => (
            <div
              key={startIndex + itemIndex}
              style={{ width: itemWidth }}
              className="virtualized-grid-item"
            >
              {renderItem ? renderItem(item, startIndex + itemIndex) : (
                <div style={{ padding: '16px' }}>
                  {typeof item === 'string' ? item : JSON.stringify(item)}
                </div>
              )}
            </div>
          ))}
          {/* Fill remaining space if needed */}
          {Array.from({ length: itemsPerRow - rowItems.length }).map((_, fillIndex) => (
            <div key={`fill-${fillIndex}`} style={{ width: itemWidth }} />
          ))}
        </div>
      </div>
    );
  }, [items, itemsPerRow, renderItem]);

  return (
    <div
      ref={containerRef}
      className={`virtualized-grid ${className}`}
      style={{ width: '100%', ...style }}
    >
      <VirtualizedList
        items={Array.from({ length: rowCount }, (_, index) => index)}
        itemHeight={itemHeight}
        height={height}
        onLoadMore={onLoadMore}
        hasNextPage={hasNextPage}
        isLoading={isLoading}
        renderItem={Row}
        {...props}
      />
    </div>
  );
};

export default VirtualizedList;
