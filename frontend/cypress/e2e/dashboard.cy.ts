describe('Dashboard', () => {
  beforeEach(() => {
    // Visit the dashboard page
    cy.visit('/');
  });

  it('displays the main dashboard elements', () => {
    // Check page title
    cy.contains('Security Dashboard').should('be.visible');
    cy.contains('Overview of your security posture and recent activity').should('be.visible');

    // Check statistics cards
    cy.contains('Total Alerts').should('be.visible');
    cy.contains('High Severity').should('be.visible');
    cy.contains('Resolved').should('be.visible');
    cy.contains('False Positives').should('be.visible');

    // Check real-time metrics section
    cy.get('[data-testid="realtime-metrics"]').should('be.visible');
    cy.contains('Real-time Metrics').should('be.visible');

    // Check charts section
    cy.contains('Alert Trends (7 days)').should('be.visible');
    cy.contains('Severity Distribution').should('be.visible');
    cy.contains('Top Alert Sources').should('be.visible');
  });

  it('navigates to alerts page', () => {
    // Click on Alerts in navigation
    cy.get('nav').contains('Alerts').click();
    
    // Should navigate to alerts page
    cy.url().should('include', '/alerts');
    cy.contains('Security Alerts').should('be.visible');
  });

  it('navigates to metrics page', () => {
    // Click on Metrics in navigation
    cy.get('nav').contains('Metrics').click();
    
    // Should navigate to metrics page
    cy.url().should('include', '/metrics');
    cy.contains('Metrics & Analytics').should('be.visible');
  });

  it('navigates to settings page', () => {
    // Click on Settings in navigation
    cy.get('nav').contains('Settings').click();
    
    // Should navigate to settings page
    cy.url().should('include', '/settings');
    cy.contains('Settings').should('be.visible');
  });

  it('toggles dark mode', () => {
    // Click theme toggle button
    cy.get('[data-testid="theme-toggle"]').click();
    
    // Check if dark mode is applied
    cy.get('html').should('have.class', 'dark');
    
    // Toggle back to light mode
    cy.get('[data-testid="theme-toggle"]').click();
    cy.get('html').should('not.have.class', 'dark');
  });

  it('shows notification bell', () => {
    // Check notification bell is visible
    cy.get('[data-testid="notification-bell"]').should('be.visible');
  });

  it('shows connection status', () => {
    // Check connection status indicator
    cy.get('[data-testid="connection-status"]').should('be.visible');
  });

  it('displays responsive design on mobile', () => {
    // Set mobile viewport
    cy.viewport(375, 667);
    
    // Check mobile navigation
    cy.get('[data-testid="mobile-menu-button"]').should('be.visible');
    
    // Open mobile menu
    cy.get('[data-testid="mobile-menu-button"]').click();
    
    // Check mobile menu items
    cy.contains('Dashboard').should('be.visible');
    cy.contains('Alerts').should('be.visible');
    cy.contains('Metrics').should('be.visible');
    cy.contains('Settings').should('be.visible');
  });

  it('handles real-time updates', () => {
    // Check if real-time metrics are displayed
    cy.get('[data-testid="realtime-metrics"]').should('be.visible');
    
    // Check for live indicator
    cy.contains('Live').should('be.visible');
  });

  it('displays charts correctly', () => {
    // Check if charts are rendered
    cy.get('canvas').should('have.length.at.least', 1);
    
    // Check chart titles
    cy.contains('Alert Trends (7 days)').should('be.visible');
    cy.contains('Severity Distribution').should('be.visible');
    cy.contains('Top Alert Sources').should('be.visible');
  });

  it('shows loading state initially', () => {
    // This test would need to be run with a slow network
    // or by intercepting the API calls
    cy.intercept('GET', '/api/v1/dashboard', { delay: 2000 }).as('dashboardData');
    cy.intercept('GET', '/api/v1/statistics', { delay: 2000 }).as('statistics');
    
    cy.visit('/');
    
    // Should show loading state
    cy.contains('Loading dashboard...').should('be.visible');
    
    // Wait for data to load
    cy.wait(['@dashboardData', '@statistics']);
    
    // Should show dashboard content
    cy.contains('Security Dashboard').should('be.visible');
  });
});
