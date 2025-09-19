// Import commands.js using ES2015 syntax:
import './commands';

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Hide fetch/XHR requests from command log
Cypress.on('window:before:load', (win) => {
  // Mock WebSocket
  win.WebSocket = class WebSocket {
    public readyState: number = WebSocket.OPEN;
    public url: string;
    public onopen: ((event: Event) => void) | null = null;
    public onclose: ((event: CloseEvent) => void) | null = null;
    public onmessage: ((event: MessageEvent) => void) | null = null;
    public onerror: ((event: Event) => void) | null = null;

    constructor(url: string) {
      this.url = url;
      // Simulate connection
      setTimeout(() => {
        this.readyState = WebSocket.OPEN;
        if (this.onopen) {
          this.onopen(new Event('open'));
        }
      }, 100);
    }

    send(data: string) {
      console.log('Mock WebSocket send:', data);
    }

    close() {
      this.readyState = WebSocket.CLOSED;
      if (this.onclose) {
        this.onclose(new CloseEvent('close'));
      }
    }
  } as any;

  // Mock IntersectionObserver
  win.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  } as any;

  // Mock ResizeObserver
  win.ResizeObserver = class ResizeObserver {
    constructor() {}
    disconnect() {}
    observe() {}
    unobserve() {}
  } as any;
});

// Add custom commands
declare global {
  namespace Cypress {
    interface Chainable {
      login(email?: string, password?: string): Chainable<void>;
      logout(): Chainable<void>;
      mockWebSocket(): Chainable<void>;
    }
  }
}
