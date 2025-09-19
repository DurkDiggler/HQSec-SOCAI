/// <reference types="cypress" />

// Custom command for login
Cypress.Commands.add('login', (email = 'admin@socagent.com', password = 'password') => {
  cy.session([email, password], () => {
    cy.visit('/login');
    cy.get('[data-testid="email-input"]').type(email);
    cy.get('[data-testid="password-input"]').type(password);
    cy.get('[data-testid="login-button"]').click();
    cy.url().should('not.include', '/login');
  });
});

// Custom command for logout
Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="user-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/login');
});

// Custom command for mocking WebSocket
Cypress.Commands.add('mockWebSocket', () => {
  cy.window().then((win) => {
    win.WebSocket = class WebSocket {
      public readyState: number = WebSocket.OPEN;
      public url: string;
      public onopen: ((event: Event) => void) | null = null;
      public onclose: ((event: CloseEvent) => void) | null = null;
      public onmessage: ((event: MessageEvent) => void) | null = null;
      public onerror: ((event: Event) => void) | null = null;

      constructor(url: string) {
        this.url = url;
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
  });
});
