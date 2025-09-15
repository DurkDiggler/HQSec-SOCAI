#!/bin/bash

# SOC Agent Demo Test Script
echo "🧪 Testing SOC Agent Demo..."

# Test health endpoints
echo "1. Testing health check..."
curl -s http://localhost:8000/healthz | jq . || echo "Health check failed"

echo -e "\n2. Testing service info..."
curl -s http://localhost:8000/ | jq . || echo "Service info failed"

echo -e "\n3. Testing readiness..."
curl -s http://localhost:8000/readyz | jq . || echo "Readiness check failed"

# Test webhook processing
echo -e "\n4. Testing Wazuh webhook..."
curl -s -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 5710, "level": 7, "description": "sshd: authentication failed"},
    "agent": {"name": "srv01"},
    "data": {"srcip": "192.168.1.100", "srcuser": "admin"},
    "full_log": "Failed password from 192.168.1.100 port 22 ssh2"
  }' | jq . || echo "Wazuh webhook failed"

echo -e "\n5. Testing CrowdStrike webhook..."
curl -s -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "crowdstrike",
    "eventType": "AuthActivityAuthFail",
    "Severity": 8,
    "LocalIP": "10.0.0.50",
    "UserName": "administrator",
    "Name": "Multiple failed login attempts"
  }' | jq . || echo "CrowdStrike webhook failed"

echo -e "\n6. Testing high-severity event..."
curl -s -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source": "wazuh",
    "rule": {"id": 1002, "level": 12, "description": "Malware detected"},
    "agent": {"name": "workstation01"},
    "data": {"srcip": "1.2.3.4", "srcuser": "user1"},
    "full_log": "Malware detected: trojan.exe from 1.2.3.4"
  }' | jq . || echo "High-severity webhook failed"

echo -e "\n✅ Demo test complete!"
