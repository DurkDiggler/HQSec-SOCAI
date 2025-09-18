#!/usr/bin/env node

/**
 * Bundle Analysis Script for SOC Agent Frontend
 * 
 * Analyzes webpack bundle size and provides optimization recommendations
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const CONFIG = {
  buildDir: 'build',
  analysisDir: 'bundle-analysis',
  thresholds: {
    totalSize: 1024 * 1024, // 1MB
    chunkSize: 250 * 1024,  // 250KB
    assetSize: 100 * 1024,  // 100KB
  },
  recommendations: {
    high: '🔴 High priority - Consider immediate optimization',
    medium: '🟡 Medium priority - Consider optimization when possible',
    low: '🟢 Low priority - Monitor for future optimization',
  },
};

// Colors for console output
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  reset: '\x1b[0m',
  bold: '\x1b[1m',
};

// Utility functions
const log = (message, color = 'white') => {
  console.log(`${colors[color]}${message}${colors.reset}`);
};

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getPriority = (size, threshold) => {
  if (size > threshold * 2) return 'high';
  if (size > threshold) return 'medium';
  return 'low';
};

// Analyze bundle size
function analyzeBundleSize() {
  log('\n📊 Bundle Size Analysis', 'cyan');
  log('=' * 50, 'cyan');

  const buildPath = path.join(process.cwd(), CONFIG.buildDir);
  
  if (!fs.existsSync(buildPath)) {
    log('❌ Build directory not found. Please run "npm run build" first.', 'red');
    process.exit(1);
  }

  const stats = {
    totalSize: 0,
    chunks: [],
    assets: [],
    recommendations: [],
  };

  // Analyze static directory
  const staticPath = path.join(buildPath, 'static');
  if (fs.existsSync(staticPath)) {
    analyzeDirectory(staticPath, stats);
  }

  // Analyze root files
  const rootFiles = fs.readdirSync(buildPath).filter(file => {
    const filePath = path.join(buildPath, file);
    return fs.statSync(filePath).isFile();
  });

  rootFiles.forEach(file => {
    const filePath = path.join(buildPath, file);
    const stats = fs.statSync(filePath);
    analyzeFile(file, stats.size, stats);
  });

  return stats;
}

// Analyze directory recursively
function analyzeDirectory(dirPath, stats) {
  const items = fs.readdirSync(dirPath);
  
  items.forEach(item => {
    const itemPath = path.join(dirPath, item);
    const itemStats = fs.statSync(itemPath);
    
    if (itemStats.isDirectory()) {
      analyzeDirectory(itemPath, stats);
    } else {
      const relativePath = path.relative(process.cwd(), itemPath);
      analyzeFile(relativePath, itemStats.size, stats);
    }
  });
}

// Analyze individual file
function analyzeFile(filePath, size, stats) {
  stats.totalSize += size;
  
  const fileInfo = {
    path: filePath,
    size: size,
    priority: getPriority(size, CONFIG.thresholds.assetSize),
  };

  // Categorize by file type
  if (filePath.endsWith('.js')) {
    stats.chunks.push(fileInfo);
  } else if (filePath.match(/\.(css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot)$/)) {
    stats.assets.push(fileInfo);
  }

  // Generate recommendations
  if (size > CONFIG.thresholds.assetSize) {
    const priority = getPriority(size, CONFIG.thresholds.assetSize);
    stats.recommendations.push({
      file: filePath,
      size: size,
      priority: priority,
      message: `${filePath} is ${formatBytes(size)} (${CONFIG.recommendations[priority]})`,
    });
  }
}

// Generate optimization recommendations
function generateRecommendations(stats) {
  log('\n💡 Optimization Recommendations', 'yellow');
  log('=' * 50, 'yellow');

  // Sort recommendations by priority
  const sortedRecommendations = stats.recommendations.sort((a, b) => {
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  // Group by priority
  const groupedRecommendations = {
    high: sortedRecommendations.filter(r => r.priority === 'high'),
    medium: sortedRecommendations.filter(r => r.priority === 'medium'),
    low: sortedRecommendations.filter(r => r.priority === 'low'),
  };

  // Display recommendations
  Object.keys(groupedRecommendations).forEach(priority => {
    const recommendations = groupedRecommendations[priority];
    if (recommendations.length > 0) {
      log(`\n${CONFIG.recommendations[priority]}`, priority === 'high' ? 'red' : priority === 'medium' ? 'yellow' : 'green');
      recommendations.forEach(rec => {
        log(`  • ${rec.file}: ${formatBytes(rec.size)}`, 'white');
      });
    }
  });

  // General recommendations
  log('\n🔧 General Optimization Tips:', 'cyan');
  log('  • Enable gzip compression on your server', 'white');
  log('  • Use CDN for static assets', 'white');
  log('  • Implement lazy loading for images and components', 'white');
  log('  • Consider code splitting for large chunks', 'white');
  log('  • Optimize images (WebP, AVIF formats)', 'white');
  log('  • Remove unused CSS and JavaScript', 'white');
  log('  • Use tree shaking to eliminate dead code', 'white');
}

// Generate detailed report
function generateReport(stats) {
  log('\n📈 Detailed Report', 'blue');
  log('=' * 50, 'blue');

  // Total size
  log(`\nTotal Bundle Size: ${formatBytes(stats.totalSize)}`, 'bold');
  
  // Size breakdown
  const jsSize = stats.chunks.reduce((sum, chunk) => sum + chunk.size, 0);
  const assetSize = stats.assets.reduce((sum, asset) => sum + asset.size, 0);
  
  log(`JavaScript: ${formatBytes(jsSize)} (${((jsSize / stats.totalSize) * 100).toFixed(1)}%)`, 'white');
  log(`Assets: ${formatBytes(assetSize)} (${((assetSize / stats.totalSize) * 100).toFixed(1)}%)`, 'white');

  // Largest chunks
  log('\n🔍 Largest JavaScript Chunks:', 'cyan');
  stats.chunks
    .sort((a, b) => b.size - a.size)
    .slice(0, 10)
    .forEach((chunk, index) => {
      const priority = getPriority(chunk.size, CONFIG.thresholds.chunkSize);
      const color = priority === 'high' ? 'red' : priority === 'medium' ? 'yellow' : 'green';
      log(`  ${index + 1}. ${chunk.path}: ${formatBytes(chunk.size)}`, color);
    });

  // Largest assets
  log('\n🖼️ Largest Assets:', 'cyan');
  stats.assets
    .sort((a, b) => b.size - a.size)
    .slice(0, 10)
    .forEach((asset, index) => {
      const priority = getPriority(asset.size, CONFIG.thresholds.assetSize);
      const color = priority === 'high' ? 'red' : priority === 'medium' ? 'yellow' : 'green';
      log(`  ${index + 1}. ${asset.path}: ${formatBytes(asset.size)}`, color);
    });
}

// Save report to file
function saveReport(stats) {
  const reportPath = path.join(process.cwd(), CONFIG.analysisDir);
  
  if (!fs.existsSync(reportPath)) {
    fs.mkdirSync(reportPath, { recursive: true });
  }

  const report = {
    timestamp: new Date().toISOString(),
    totalSize: stats.totalSize,
    chunks: stats.chunks,
    assets: stats.assets,
    recommendations: stats.recommendations,
    thresholds: CONFIG.thresholds,
  };

  const reportFile = path.join(reportPath, 'bundle-analysis.json');
  fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
  
  log(`\n📄 Report saved to: ${reportFile}`, 'green');
}

// Main function
function main() {
  log('🚀 SOC Agent Bundle Analyzer', 'bold');
  log('=' * 50, 'bold');

  try {
    // Analyze bundle
    const stats = analyzeBundleSize();
    
    // Generate report
    generateReport(stats);
    
    // Generate recommendations
    generateRecommendations(stats);
    
    // Save report
    saveReport(stats);
    
    // Summary
    log('\n✅ Analysis Complete!', 'green');
    log(`Total bundle size: ${formatBytes(stats.totalSize)}`, 'white');
    log(`Recommendations: ${stats.recommendations.length}`, 'white');
    
  } catch (error) {
    log(`❌ Analysis failed: ${error.message}`, 'red');
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  analyzeBundleSize,
  generateRecommendations,
  generateReport,
  saveReport,
};
