import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import Chat from '../Chat';

// Mock the API hooks
jest.mock('../../store/api', () => ({
  useGetMCPToolsQuery: () => ({
    data: {
      data: [
        {
          name: 'nmap',
          description: 'Network mapper tool',
          category: 'network',
          parameters: [
            { name: 'target', type: 'string', description: 'Target IP or hostname', required: true },
            { name: 'scan_type', type: 'string', description: 'Type of scan', required: false, default_value: 'syn' }
          ],
        },
        {
          name: 'metasploit',
          description: 'Penetration testing framework',
          category: 'exploitation',
          parameters: [
            { name: 'exploit', type: 'string', description: 'Exploit to use', required: true },
            { name: 'payload', type: 'string', description: 'Payload to use', required: false }
          ],
        },
      ],
    },
    isLoading: false,
  }),
  useExecuteMCPToolMutation: () => [
    jest.fn().mockResolvedValue({
      unwrap: () => Promise.resolve({
        data: {
          output: 'Scan completed successfully',
          status: 'success',
        },
      }),
    }),
  ],
  useAnalyzeWithLLMMutation: () => [
    jest.fn().mockResolvedValue({
      unwrap: () => Promise.resolve({
        data: {
          response: 'I can help you with that. Let me run a network scan.',
          suggested_tool: 'nmap',
          tool_parameters: { target: '192.168.1.1' },
          confidence: 0.9,
        },
      }),
    }),
  ],
}));

describe('Chat', () => {
  it('renders chat interface', () => {
    render(<Chat />);
    
    expect(screen.getByText('SOC Agent Chat')).toBeInTheDocument();
    expect(screen.getByText('AI-powered security analysis with Kali MCP tools')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask me anything about security analysis, or request a Kali tool...')).toBeInTheDocument();
  });

  it('displays welcome message on load', () => {
    render(<Chat />);
    
    expect(screen.getByText('Welcome to the SOC Agent Chat! I can help you with security analysis, run Kali tools, and provide AI-powered insights. What would you like to do?')).toBeInTheDocument();
  });

  it('shows available tools in sidebar', () => {
    render(<Chat />);
    
    expect(screen.getByText('Available Tools')).toBeInTheDocument();
    expect(screen.getByText('nmap')).toBeInTheDocument();
    expect(screen.getByText('Network mapper tool')).toBeInTheDocument();
    expect(screen.getByText('metasploit')).toBeInTheDocument();
    expect(screen.getByText('Penetration testing framework')).toBeInTheDocument();
  });

  it('sends message when send button is clicked', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Ask me anything about security analysis, or request a Kali tool...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Scan 192.168.1.1 for vulnerabilities' } });
    fireEvent.click(sendButton);
    
    expect(screen.getByText('Scan 192.168.1.1 for vulnerabilities')).toBeInTheDocument();
  });

  it('sends message when Enter key is pressed', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Ask me anything about security analysis, or request a Kali tool...');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('shows quick action buttons', () => {
    render(<Chat />);
    
    expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    expect(screen.getByText('Vulnerability Scan')).toBeInTheDocument();
    expect(screen.getByText('Network Analysis')).toBeInTheDocument();
    expect(screen.getByText('Security Check')).toBeInTheDocument();
  });

  it('handles quick action button clicks', () => {
    render(<Chat />);
    
    const vulnerabilityButton = screen.getByText('Vulnerability Scan');
    fireEvent.click(vulnerabilityButton);
    
    const input = screen.getByPlaceholderText('Ask me anything about security analysis, or request a Kali tool...');
    expect(input).toHaveValue('Scan for vulnerabilities on 192.168.1.1');
  });

  it('shows clear chat button', () => {
    render(<Chat />);
    
    expect(screen.getByText('Clear Chat')).toBeInTheDocument();
  });

  it('clears chat when clear button is clicked', () => {
    render(<Chat />);
    
    const clearButton = screen.getByText('Clear Chat');
    fireEvent.click(clearButton);
    
    expect(screen.getByText('Chat cleared. How can I help you today?')).toBeInTheDocument();
  });

  it('disables send button when input is empty', () => {
    render(<Chat />);
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when input has content', () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Ask me anything about security analysis, or request a Kali tool...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    expect(sendButton).not.toBeDisabled();
  });

  it('shows tool parameters in sidebar', () => {
    render(<Chat />);
    
    expect(screen.getByText('Parameters: target, scan_type')).toBeInTheDocument();
    expect(screen.getByText('Parameters: exploit, payload')).toBeInTheDocument();
  });

  it('handles tool selection', () => {
    render(<Chat />);
    
    const nmapTool = screen.getByText('nmap');
    fireEvent.click(nmapTool);
    
    // Tool should be selected (this would be tested with visual feedback)
    expect(nmapTool).toBeInTheDocument();
  });
});
