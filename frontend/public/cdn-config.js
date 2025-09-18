/**
 * CDN Configuration for SOC Agent Frontend
 * 
 * This file contains CDN settings and fallback configurations
 * for static assets and external dependencies.
 */

// CDN Configuration
const CDN_CONFIG = {
  // Primary CDN (e.g., CloudFlare, AWS CloudFront, etc.)
  primary: {
    baseUrl: process.env.REACT_APP_CDN_URL || 'https://cdn.socagent.com',
    fallback: true,
    timeout: 5000,
  },
  
  // Fallback CDN (e.g., jsDelivr, unpkg, etc.)
  fallback: {
    baseUrl: 'https://cdn.jsdelivr.net/npm',
    timeout: 3000,
  },
  
  // Local fallback
  local: {
    baseUrl: '/static',
    timeout: 1000,
  },
  
  // External CDN configurations
  external: {
    // Google Fonts
    fonts: {
      baseUrl: 'https://fonts.googleapis.com',
      css: 'https://fonts.googleapis.com/css2',
      display: 'swap',
    },
    
    // Font Awesome (if needed)
    fontawesome: {
      baseUrl: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome',
      version: '6.4.0',
    },
    
    // Chart.js (if needed)
    chartjs: {
      baseUrl: 'https://cdn.jsdelivr.net/npm/chart.js',
      version: '4.4.0',
    },
  },
};

// Asset loading configuration
const ASSET_CONFIG = {
  // Image optimization settings
  images: {
    formats: ['webp', 'avif', 'jpg', 'png'],
    quality: 80,
    maxWidth: 1920,
    maxHeight: 1080,
    lazy: true,
    placeholder: true,
  },
  
  // Font loading settings
  fonts: {
    preload: true,
    display: 'swap',
    fallback: true,
  },
  
  // Script loading settings
  scripts: {
    async: true,
    defer: true,
    crossorigin: 'anonymous',
  },
  
  // CSS loading settings
  styles: {
    preload: true,
    media: 'all',
    crossorigin: 'anonymous',
  },
};

// Preload critical resources
const CRITICAL_RESOURCES = [
  // Critical CSS
  '/static/css/critical.css',
  
  // Critical fonts
  '/static/fonts/inter-var.woff2',
  
  // Critical images
  '/static/images/logo.svg',
  '/static/images/hero-bg.webp',
];

// Lazy load non-critical resources
const LAZY_RESOURCES = [
  // Non-critical CSS
  '/static/css/non-critical.css',
  
  // Non-critical scripts
  '/static/js/analytics.js',
  '/static/js/chat-widget.js',
  
  // Non-critical images
  '/static/images/backgrounds/',
  '/static/images/icons/',
];

/**
 * Load resource with fallback
 */
async function loadResource(url, options = {}) {
  const { timeout = 5000, fallback = true } = options;
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(url, {
      signal: controller.signal,
      ...options,
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    if (fallback && url.startsWith(CDN_CONFIG.primary.baseUrl)) {
      // Try fallback CDN
      const fallbackUrl = url.replace(CDN_CONFIG.primary.baseUrl, CDN_CONFIG.fallback.baseUrl);
      return loadResource(fallbackUrl, { ...options, fallback: false });
    }
    
    throw error;
  }
}

/**
 * Preload critical resources
 */
function preloadCriticalResources() {
  CRITICAL_RESOURCES.forEach(resource => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = resource;
    
    if (resource.endsWith('.css')) {
      link.as = 'style';
      link.onload = () => {
        link.rel = 'stylesheet';
      };
    } else if (resource.endsWith('.woff2') || resource.endsWith('.woff')) {
      link.as = 'font';
      link.type = 'font/woff2';
      link.crossOrigin = 'anonymous';
    } else if (resource.endsWith('.js')) {
      link.as = 'script';
    } else if (resource.match(/\.(jpg|jpeg|png|webp|avif)$/)) {
      link.as = 'image';
    }
    
    document.head.appendChild(link);
  });
}

/**
 * Lazy load non-critical resources
 */
function lazyLoadResources() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const element = entry.target;
        const resource = element.dataset.resource;
        
        if (resource) {
          loadResource(resource).then(() => {
            element.classList.add('loaded');
          }).catch(error => {
            console.warn(`Failed to load resource: ${resource}`, error);
          });
        }
        
        observer.unobserve(element);
      }
    });
  }, {
    rootMargin: '50px',
  });
  
  LAZY_RESOURCES.forEach(resource => {
    const element = document.createElement('div');
    element.dataset.resource = resource;
    element.style.display = 'none';
    document.body.appendChild(element);
    observer.observe(element);
  });
}

/**
 * Initialize CDN configuration
 */
function initializeCDN() {
  // Preload critical resources
  preloadCriticalResources();
  
  // Lazy load non-critical resources
  lazyLoadResources();
  
  // Set up service worker for caching
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('Service Worker registered:', registration);
      })
      .catch(error => {
        console.warn('Service Worker registration failed:', error);
      });
  }
}

/**
 * Get optimized image URL
 */
function getOptimizedImageUrl(src, options = {}) {
  const { width, height, quality = 80, format = 'webp' } = options;
  
  if (src.startsWith('data:') || src.startsWith('http')) {
    return src;
  }
  
  const params = new URLSearchParams();
  if (width) params.append('w', width);
  if (height) params.append('h', height);
  if (quality) params.append('q', quality);
  if (format) params.append('f', format);
  
  const queryString = params.toString();
  return queryString ? `${CDN_CONFIG.primary.baseUrl}${src}?${queryString}` : `${CDN_CONFIG.primary.baseUrl}${src}`;
}

/**
 * Get font URL with display swap
 */
function getFontUrl(fontFamily, weights = [400, 500, 600, 700]) {
  const weightsStr = weights.join(';');
  return `${CDN_CONFIG.external.fonts.css}?family=${fontFamily}:wght@${weightsStr}&display=swap`;
}

// Export configuration
window.CDN_CONFIG = {
  ...CDN_CONFIG,
  loadResource,
  preloadCriticalResources,
  lazyLoadResources,
  initializeCDN,
  getOptimizedImageUrl,
  getFontUrl,
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeCDN);
} else {
  initializeCDN();
}

export default CDN_CONFIG;
