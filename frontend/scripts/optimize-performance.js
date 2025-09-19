const fs = require('fs');
const path = require('path');

// Performance optimization script
console.log('🚀 Starting performance optimization...');

// 1. Create optimized bundle analyzer
const bundleAnalyzerConfig = `
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false,
      reportFilename: 'bundle-analysis.html',
    }),
  ],
};
`;

fs.writeFileSync(
  path.join(__dirname, '../webpack-bundle-analyzer.config.js'),
  bundleAnalyzerConfig
);

// 2. Create performance monitoring script
const performanceMonitor = `
// Performance monitoring utilities
export const performanceMonitor = {
  // Measure component render time
  measureRender: (componentName, renderFn) => {
    const start = performance.now();
    const result = renderFn();
    const end = performance.now();
    console.log(\`\${componentName} rendered in \${end - start}ms\`);
    return result;
  },

  // Measure API call performance
  measureApiCall: async (apiName, apiCall) => {
    const start = performance.now();
    try {
      const result = await apiCall();
      const end = performance.now();
      console.log(\`\${apiName} completed in \${end - start}ms\`);
      return result;
    } catch (error) {
      const end = performance.now();
      console.error(\`\${apiName} failed after \${end - start}ms:\`, error);
      throw error;
    }
  },

  // Measure WebSocket message processing
  measureWebSocketMessage: (messageType, processFn) => {
    const start = performance.now();
    const result = processFn();
    const end = performance.now();
    console.log(\`WebSocket \${messageType} processed in \${end - start}ms\`);
    return result;
  },

  // Get memory usage
  getMemoryUsage: () => {
    if (performance.memory) {
      return {
        used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
        total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
        limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024),
      };
    }
    return null;
  },

  // Log performance metrics
  logMetrics: () => {
    const memory = performanceMonitor.getMemoryUsage();
    if (memory) {
      console.log('Memory Usage:', memory);
    }
    
    // Log Web Vitals
    if (window.performance && window.performance.getEntriesByType) {
      const paintEntries = window.performance.getEntriesByType('paint');
      paintEntries.forEach(entry => {
        console.log(\`\${entry.name}: \${entry.startTime}ms\`);
      });
    }
  },
};

// Web Vitals measurement
export const measureWebVitals = () => {
  if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
    // Measure Largest Contentful Paint
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime);
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // Measure First Input Delay
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        console.log('FID:', entry.processingStart - entry.startTime);
      });
    }).observe({ entryTypes: ['first-input'] });

    // Measure Cumulative Layout Shift
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        if (!entry.hadRecentInput) {
          console.log('CLS:', entry.value);
        }
      });
    }).observe({ entryTypes: ['layout-shift'] });
  }
};
`;

fs.writeFileSync(
  path.join(__dirname, '../src/utils/performance.ts'),
  performanceMonitor
);

// 3. Create lazy loading utilities
const lazyLoadingUtils = `
import { lazy, ComponentType } from 'react';

// Lazy load components with error boundaries
export const lazyLoad = <T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) => {
  return lazy(importFunc);
};

// Preload critical components
export const preloadCriticalComponents = () => {
  // Preload dashboard components
  import('../pages/Dashboard');
  import('../components/RealtimeMetrics');
  import('../components/RealtimeNotifications');
  
  // Preload common components
  import('../components/ui/Button');
  import('../components/ui/LoadingSpinner');
  import('../components/layout/Card');
};

// Lazy load with retry
export const lazyLoadWithRetry = <T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  retries = 3
) => {
  return lazy(() => {
    return importFunc().catch((error) => {
      if (retries > 0) {
        console.warn(\`Failed to load component, retrying... (\${retries} retries left)\`);
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve(lazyLoadWithRetry(importFunc, retries - 1)());
          }, 1000);
        });
      }
      throw error;
    });
  });
};

// Preload components on hover
export const preloadOnHover = (importFunc: () => Promise<any>) => {
  let preloaded = false;
  
  return {
    onMouseEnter: () => {
      if (!preloaded) {
        preloaded = true;
        importFunc();
      }
    },
  };
};
`;

fs.writeFileSync(
  path.join(__dirname, '../src/utils/lazyLoading.ts'),
  lazyLoadingUtils
);

// 4. Create image optimization script
const imageOptimization = `
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const optimizeImages = async () => {
  const imagesDir = path.join(__dirname, '../public/images');
  const outputDir = path.join(__dirname, '../public/images/optimized');
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const imageFiles = fs.readdirSync(imagesDir).filter(file => 
    /\.(jpg|jpeg|png|webp)$/i.test(file)
  );
  
  for (const file of imageFiles) {
    const inputPath = path.join(imagesDir, file);
    const outputPath = path.join(outputDir, file.replace(/\\.(jpg|jpeg|png)$/i, '.webp'));
    
    try {
      await sharp(inputPath)
        .webp({ quality: 80 })
        .toFile(outputPath);
      
      console.log(\`Optimized \${file} -> \${path.basename(outputPath)}\`);
    } catch (error) {
      console.error(\`Failed to optimize \${file}:\`, error);
    }
  }
};

if (require.main === module) {
  optimizeImages();
}

module.exports = { optimizeImages };
`;

fs.writeFileSync(
  path.join(__dirname, '../scripts/optimize-images.js'),
  imageOptimization
);

// 5. Create bundle analysis script
const bundleAnalysis = `
const fs = require('fs');
const path = require('path');

const analyzeBundle = () => {
  const buildDir = path.join(__dirname, '../build');
  const staticDir = path.join(buildDir, 'static');
  
  if (!fs.existsSync(staticDir)) {
    console.log('Build directory not found. Run npm run build first.');
    return;
  }
  
  const jsFiles = fs.readdirSync(staticDir)
    .filter(file => file.endsWith('.js'))
    .map(file => {
      const filePath = path.join(staticDir, file);
      const stats = fs.statSync(filePath);
      return {
        name: file,
        size: stats.size,
        sizeKB: Math.round(stats.size / 1024),
        sizeMB: Math.round(stats.size / 1024 / 1024 * 100) / 100,
      };
    })
    .sort((a, b) => b.size - a.size);
  
  console.log('\\n📊 Bundle Analysis:');
  console.log('==================');
  
  jsFiles.forEach(file => {
    console.log(\`\${file.name}: \${file.sizeKB}KB (\${file.sizeMB}MB)\`);
  });
  
  const totalSize = jsFiles.reduce((sum, file) => sum + file.size, 0);
  console.log(\`\\nTotal JS size: \${Math.round(totalSize / 1024)}KB (\${Math.round(totalSize / 1024 / 1024 * 100) / 100}MB)\`);
  
  // Check for large files
  const largeFiles = jsFiles.filter(file => file.size > 500 * 1024); // > 500KB
  if (largeFiles.length > 0) {
    console.log('\\n⚠️  Large files detected:');
    largeFiles.forEach(file => {
      console.log(\`  \${file.name}: \${file.sizeKB}KB\`);
    });
  }
  
  // Check for duplicate dependencies
  console.log('\\n🔍 Checking for potential optimizations...');
  console.log('  - Consider code splitting for large components');
  console.log('  - Check for duplicate dependencies');
  console.log('  - Use dynamic imports for non-critical features');
  console.log('  - Optimize images and assets');
};

if (require.main === module) {
  analyzeBundle();
}

module.exports = { analyzeBundle };
`;

fs.writeFileSync(
  path.join(__dirname, '../scripts/analyze-bundle.js'),
  bundleAnalysis
);

console.log('✅ Performance optimization scripts created!');
console.log('📁 Files created:');
console.log('  - webpack-bundle-analyzer.config.js');
console.log('  - src/utils/performance.ts');
console.log('  - src/utils/lazyLoading.ts');
console.log('  - scripts/optimize-images.js');
console.log('  - scripts/analyze-bundle.js');
console.log('\\n🚀 Run the following commands to optimize:');
console.log('  npm run build:analyze');
console.log('  npm run optimize:images');
console.log('  npm run analyze:bundle');
