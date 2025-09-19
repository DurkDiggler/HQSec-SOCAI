const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Starting production build...');

// 1. Clean build directory
console.log('🧹 Cleaning build directory...');
if (fs.existsSync('build')) {
  fs.rmSync('build', { recursive: true, force: true });
}

// 2. Set production environment
process.env.NODE_ENV = 'production';
process.env.GENERATE_SOURCEMAP = 'false';
process.env.INLINE_RUNTIME_CHUNK = 'false';

// 3. Run build
console.log('🔨 Building application...');
try {
  execSync('npm run build', { stdio: 'inherit' });
  console.log('✅ Build completed successfully!');
} catch (error) {
  console.error('❌ Build failed:', error.message);
  process.exit(1);
}

// 4. Analyze bundle size
console.log('📊 Analyzing bundle size...');
const buildDir = path.join(__dirname, '../build');
const staticDir = path.join(buildDir, 'static');

if (fs.existsSync(staticDir)) {
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

  console.log('\n📊 Bundle Analysis:');
  console.log('==================');
  
  jsFiles.forEach(file => {
    console.log(`${file.name}: ${file.sizeKB}KB (${file.sizeMB}MB)`);
  });
  
  const totalSize = jsFiles.reduce((sum, file) => sum + file.size, 0);
  console.log(`\nTotal JS size: ${Math.round(totalSize / 1024)}KB (${Math.round(totalSize / 1024 / 1024 * 100) / 100}MB)`);
  
  // Check for large files
  const largeFiles = jsFiles.filter(file => file.size > 500 * 1024); // > 500KB
  if (largeFiles.length > 0) {
    console.log('\n⚠️  Large files detected:');
    largeFiles.forEach(file => {
      console.log(`  ${file.name}: ${file.sizeKB}KB`);
    });
  }
}

// 5. Create build info
const buildInfo = {
  timestamp: new Date().toISOString(),
  version: process.env.npm_package_version || '1.0.0',
  nodeVersion: process.version,
  buildTime: Date.now(),
  environment: 'production',
  features: {
    typescript: true,
    redux: true,
    websocket: true,
    realtime: true,
    testing: true,
  },
};

fs.writeFileSync(
  path.join(buildDir, 'build-info.json'),
  JSON.stringify(buildInfo, null, 2)
);

console.log('📝 Build info saved to build-info.json');

// 6. Create deployment checklist
const deploymentChecklist = `
# 🚀 Production Deployment Checklist

## Pre-deployment
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance audit completed
- [ ] Bundle size optimized
- [ ] Environment variables configured
- [ ] SSL certificates ready
- [ ] Database migrations ready

## Deployment
- [ ] Build artifacts uploaded
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] SSL certificates installed
- [ ] CDN configured
- [ ] Monitoring enabled

## Post-deployment
- [ ] Health checks passing
- [ ] Performance monitoring active
- [ ] Error tracking enabled
- [ ] Analytics working
- [ ] User acceptance testing
- [ ] Documentation updated

## Rollback Plan
- [ ] Previous version available
- [ ] Database rollback plan
- [ ] Monitoring alerts configured
- [ ] Team notified of rollback procedure

Build completed: ${new Date().toISOString()}
Version: ${buildInfo.version}
`;

fs.writeFileSync(
  path.join(buildDir, 'DEPLOYMENT_CHECKLIST.md'),
  deploymentChecklist
);

console.log('📋 Deployment checklist created');

// 7. Create performance report
const performanceReport = `
# 📊 Performance Report

## Bundle Analysis
${jsFiles.map(file => `- ${file.name}: ${file.sizeKB}KB`).join('\n')}

## Recommendations
${largeFiles.length > 0 ? 
  `- Consider code splitting for large files: ${largeFiles.map(f => f.name).join(', ')}` : 
  '- Bundle size is optimized'
}
- Enable gzip compression
- Use CDN for static assets
- Implement service worker for caching

## Build Info
- Build Time: ${new Date().toISOString()}
- Total Size: ${Math.round(totalSize / 1024)}KB
- Files: ${jsFiles.length}
- Large Files: ${largeFiles.length}
`;

fs.writeFileSync(
  path.join(buildDir, 'PERFORMANCE_REPORT.md'),
  performanceReport
);

console.log('📈 Performance report created');

console.log('\n🎉 Production build completed successfully!');
console.log('📁 Build artifacts in: build/');
console.log('📋 Next steps:');
console.log('  1. Review DEPLOYMENT_CHECKLIST.md');
console.log('  2. Check PERFORMANCE_REPORT.md');
console.log('  3. Deploy to production environment');
console.log('  4. Monitor application health');
