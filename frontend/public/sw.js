/**
 * Service Worker for SOC Agent Frontend
 * 
 * Provides caching, offline support, and performance optimizations
 */

const CACHE_NAME = 'soc-agent-v1.0.0';
const STATIC_CACHE = 'soc-agent-static-v1.0.0';
const DYNAMIC_CACHE = 'soc-agent-dynamic-v1.0.0';
const API_CACHE = 'soc-agent-api-v1.0.0';

// Cache strategies
const CACHE_STRATEGIES = {
  // Static assets - Cache First
  static: {
    strategy: 'cacheFirst',
    cacheName: STATIC_CACHE,
    maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
  },
  
  // API responses - Network First
  api: {
    strategy: 'networkFirst',
    cacheName: API_CACHE,
    maxAge: 5 * 60 * 1000, // 5 minutes
  },
  
  // Images - Cache First with fallback
  images: {
    strategy: 'cacheFirst',
    cacheName: STATIC_CACHE,
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
  },
  
  // HTML pages - Network First
  pages: {
    strategy: 'networkFirst',
    cacheName: DYNAMIC_CACHE,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
  },
};

// Critical resources to cache immediately
const CRITICAL_RESOURCES = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/images/logo.svg',
  '/manifest.json',
];

// Resources to cache on demand
const CACHE_PATTERNS = [
  // Static assets
  {
    pattern: /\.(css|js|woff2?|ttf|eot)$/,
    strategy: 'static',
  },
  
  // Images
  {
    pattern: /\.(jpg|jpeg|png|gif|webp|avif|svg)$/,
    strategy: 'images',
  },
  
  // API endpoints
  {
    pattern: /^\/api\/v1\//,
    strategy: 'api',
  },
  
  // HTML pages
  {
    pattern: /\.html$/,
    strategy: 'pages',
  },
];

// Install event - cache critical resources
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('Caching critical resources...');
        return cache.addAll(CRITICAL_RESOURCES);
      })
      .then(() => {
        console.log('Critical resources cached successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Failed to cache critical resources:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && 
                cacheName !== DYNAMIC_CACHE && 
                cacheName !== API_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  // Determine cache strategy
  const strategy = getCacheStrategy(url.pathname);
  
  if (strategy) {
    event.respondWith(handleRequest(request, strategy));
  }
});

// Get cache strategy for a given path
function getCacheStrategy(pathname) {
  for (const pattern of CACHE_PATTERNS) {
    if (pattern.pattern.test(pathname)) {
      return CACHE_STRATEGIES[pattern.strategy];
    }
  }
  return null;
}

// Handle request with appropriate strategy
async function handleRequest(request, strategy) {
  const { strategy: strategyName, cacheName, maxAge } = strategy;
  
  try {
    switch (strategyName) {
      case 'cacheFirst':
        return await cacheFirst(request, cacheName, maxAge);
      case 'networkFirst':
        return await networkFirst(request, cacheName, maxAge);
      case 'networkOnly':
        return await fetch(request);
      case 'cacheOnly':
        return await caches.match(request);
      default:
        return await fetch(request);
    }
  } catch (error) {
    console.error('Request handling error:', error);
    
    // Fallback to cache or offline page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return await caches.match('/offline.html') || new Response('Offline', { status: 503 });
    }
    
    throw error;
  }
}

// Cache First strategy
async function cacheFirst(request, cacheName, maxAge) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    // Check if cache is still valid
    const cacheTime = cachedResponse.headers.get('sw-cache-time');
    if (cacheTime && Date.now() - parseInt(cacheTime) < maxAge) {
      return cachedResponse;
    }
  }
  
  // Fetch from network
  const networkResponse = await fetch(request);
  
  if (networkResponse.ok) {
    // Clone response and add cache timestamp
    const responseToCache = networkResponse.clone();
    responseToCache.headers.set('sw-cache-time', Date.now().toString());
    
    // Cache the response
    await cache.put(request, responseToCache);
  }
  
  return networkResponse;
}

// Network First strategy
async function networkFirst(request, cacheName, maxAge) {
  const cache = await caches.open(cacheName);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Clone response and add cache timestamp
      const responseToCache = networkResponse.clone();
      responseToCache.headers.set('sw-cache-time', Date.now().toString());
      
      // Cache the response
      await cache.put(request, responseToCache);
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      // Check if cache is still valid
      const cacheTime = cachedResponse.headers.get('sw-cache-time');
      if (cacheTime && Date.now() - parseInt(cacheTime) < maxAge) {
        return cachedResponse;
      }
    }
    
    throw error;
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// Background sync implementation
async function doBackgroundSync() {
  try {
    // Get pending actions from IndexedDB
    const pendingActions = await getPendingActions();
    
    for (const action of pendingActions) {
      try {
        await processPendingAction(action);
        await removePendingAction(action.id);
      } catch (error) {
        console.error('Failed to process pending action:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    
    const options = {
      body: data.body || 'New notification',
      icon: data.icon || '/icon-192x192.png',
      badge: data.badge || '/icon-192x192.png',
      tag: data.tag || 'soc-agent-notification',
      data: data.data || {},
      actions: data.actions || [],
      requireInteraction: data.requireInteraction || false,
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'SOC Agent', options)
    );
  }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action) {
    // Handle specific action
    handleNotificationAction(event.action, event.notification.data);
  } else {
    // Default click behavior
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Handle notification actions
function handleNotificationAction(action, data) {
  switch (action) {
    case 'view-alerts':
      clients.openWindow('/alerts');
      break;
    case 'view-dashboard':
      clients.openWindow('/');
      break;
    default:
      clients.openWindow('/');
  }
}

// Utility functions for IndexedDB operations
async function getPendingActions() {
  // Implementation would depend on your IndexedDB setup
  return [];
}

async function processPendingAction(action) {
  // Process the pending action
  console.log('Processing pending action:', action);
}

async function removePendingAction(actionId) {
  // Remove the processed action
  console.log('Removing pending action:', actionId);
}

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('Service Worker loaded successfully');
