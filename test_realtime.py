#!/usr/bin/env python3
"""Test script for real-time capabilities."""

import asyncio
import json
import time
import websockets
import requests
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/v1/realtime/ws"

async def test_websocket():
    """Test WebSocket connection and messaging."""
    print("🔌 Testing WebSocket connection...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Test subscription
            subscribe_msg = {
                "type": "subscribe",
                "channels": ["alerts", "notifications"]
            }
            await websocket.send(json.dumps(subscribe_msg))
            print("📡 Sent subscription message")
            
            # Test ping
            ping_msg = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(ping_msg))
            print("🏓 Sent ping message")
            
            # Listen for messages
            print("👂 Listening for messages (5 seconds)...")
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📨 Received message: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("⏰ No messages received in 5 seconds")
            
            print("✅ WebSocket test completed")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

def test_api_endpoints():
    """Test real-time API endpoints."""
    print("\n🌐 Testing API endpoints...")
    
    # Test status endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/realtime/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint: {data.get('enabled', False)}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
    
    # Test channels endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/realtime/channels")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Channels endpoint: {len(data.get('channels', []))} channels")
        else:
            print(f"❌ Channels endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Channels endpoint error: {e}")
    
    # Test alert streaming
    try:
        response = requests.post(f"{BASE_URL}/api/v1/realtime/test/alert")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test alert sent: {data.get('message', 'Unknown')}")
        else:
            print(f"❌ Test alert failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Test alert error: {e}")
    
    # Test notification streaming
    try:
        response = requests.post(f"{BASE_URL}/api/v1/realtime/test/notification")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test notification sent: {data.get('message', 'Unknown')}")
        else:
            print(f"❌ Test notification failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Test notification error: {e}")

def test_sse():
    """Test Server-Sent Events."""
    print("\n📡 Testing Server-Sent Events...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/realtime/events", stream=True, timeout=5)
        if response.status_code == 200:
            print("✅ SSE connection established")
            
            # Read a few lines
            lines_read = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"📨 SSE data: {line[:100]}...")
                    lines_read += 1
                    if lines_read >= 3:  # Read first 3 lines
                        break
        else:
            print(f"❌ SSE connection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ SSE test error: {e}")

async def main():
    """Run all tests."""
    print("🚀 Starting Real-time Capabilities Test")
    print("=" * 50)
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test WebSocket
    await test_websocket()
    
    # Test SSE
    test_sse()
    
    print("\n" + "=" * 50)
    print("✅ Real-time capabilities test completed!")
    print("\nTo see real-time updates in action:")
    print("1. Open http://localhost:3000 in your browser")
    print("2. Watch the dashboard for real-time alerts")
    print("3. Run: curl -X POST http://localhost:8000/api/v1/realtime/test/alert")

if __name__ == "__main__":
    asyncio.run(main())
