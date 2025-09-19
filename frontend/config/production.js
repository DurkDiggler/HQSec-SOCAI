// Production configuration
module.exports = {
  // API Configuration
  API_URL: 'https://api.socagent.com/api/v1',
  WS_URL: 'wss://api.socagent.com/ws',
  
  // Feature Flags
  ENABLE_ANALYTICS: true,
  ENABLE_ERROR_REPORTING: true,
  ENABLE_PERFORMANCE_MONITORING: true,
  ENABLE_WEB_VITALS: true,
  
  // Build Configuration
  GENERATE_SOURCEMAP: false,
  INLINE_RUNTIME_CHUNK: false,
  
  // Performance
  ENABLE_BUNDLE_ANALYZER: false,
  ENABLE_COMPRESSION: true,
  ENABLE_OPTIMIZATION: true,
  
  // Security
  ENABLE_CSP: true,
  ENABLE_HSTS: true,
  
  // Monitoring
  ENABLE_SENTRY: true,
  SENTRY_DSN: process.env.SENTRY_DSN,
};
