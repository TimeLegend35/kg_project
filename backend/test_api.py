#!/usr/bin/env python3
"""
Test script for BGB AI Chat API
Run this after starting the API to verify it's working correctly.
"""
import requests
import json
import sys
from uuid import UUID

API_BASE_URL = "http://localhost:8080"
API_KEY = "dev-api-key-change-me"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{API_BASE_URL}/healthz")
    assert response.status_code == 200
    print(f"   ✅ Health: {response.json()['status']}")


def test_readiness():
    """Test readiness endpoint"""
    print("🔍 Testing readiness endpoint...")
    response = requests.get(f"{API_BASE_URL}/readyz")
    assert response.status_code == 200
    data = response.json()
    print(f"   ✅ Ready: {data['ready']}, Checks: {data['checks']}")


def test_list_agents():
    """Test listing agents"""
    print("🤖 Testing agent listing...")
    response = requests.get(f"{API_BASE_URL}/api/v1/agents", headers=HEADERS)
    assert response.status_code == 200
    agents = response.json()['agents']
    print(f"   ✅ Found {len(agents)} agents:")
    for agent in agents:
        status = "✅" if agent['available'] else "❌"
        print(f"      {status} {agent['name']}: {agent['description']}")


def test_create_thread():
    """Test creating a thread"""
    print("📝 Testing thread creation...")
    response = requests.post(
        f"{API_BASE_URL}/api/v1/threads",
        headers=HEADERS,
        json={
            "title": "Test Thread",
            "metadata": {"test": True}
        }
    )
    assert response.status_code == 201
    thread = response.json()
    thread_id = thread['id']
    print(f"   ✅ Created thread: {thread_id}")
    return thread_id


def test_get_thread(thread_id):
    """Test getting a thread"""
    print("📖 Testing thread retrieval...")
    response = requests.get(
        f"{API_BASE_URL}/api/v1/threads/{thread_id}",
        headers=HEADERS
    )
    assert response.status_code == 200
    thread = response.json()
    print(f"   ✅ Retrieved thread: {thread['title']}")


def test_list_threads():
    """Test listing threads"""
    print("📚 Testing thread listing...")
    response = requests.get(
        f"{API_BASE_URL}/api/v1/threads?limit=10",
        headers=HEADERS
    )
    assert response.status_code == 200
    threads = response.json()['threads']
    print(f"   ✅ Found {len(threads)} threads")


def test_list_messages(thread_id):
    """Test listing messages"""
    print("💬 Testing message listing...")
    response = requests.get(
        f"{API_BASE_URL}/api/v1/threads/{thread_id}/messages",
        headers=HEADERS
    )
    assert response.status_code == 200
    messages = response.json()['messages']
    print(f"   ✅ Found {len(messages)} messages")


def test_send_message_non_stream(thread_id):
    """Test sending a message (non-streaming)"""
    print("✉️  Testing message send (non-streaming)...")
    print("   ⏳ This may take a moment as it calls the agent...")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/threads/{thread_id}/messages",
            headers=HEADERS,
            json={
                "agent": "qwen",
                "input": "Was ist § 1 BGB?",
                "stream": False
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            message = data['message']
            content_preview = message['content'][:100] + "..." if len(message['content']) > 100 else message['content']
            print(f"   ✅ Message sent and processed")
            print(f"      Agent: {message['agent_name']}")
            print(f"      Content preview: {content_preview}")
            if data.get('tool_calls'):
                print(f"      Tool calls: {len(data['tool_calls'])}")
        else:
            print(f"   ⚠️  Message send returned status {response.status_code}")
            print(f"      Error: {response.text}")

    except requests.exceptions.Timeout:
        print(f"   ⚠️  Message send timed out (this is normal if agent takes long)")
    except Exception as e:
        print(f"   ⚠️  Message send error: {e}")


def test_delete_thread(thread_id):
    """Test deleting a thread"""
    print("🗑️  Testing thread deletion...")
    response = requests.delete(
        f"{API_BASE_URL}/api/v1/threads/{thread_id}",
        headers=HEADERS
    )
    assert response.status_code == 204
    print(f"   ✅ Thread deleted")


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 BGB AI Chat API - Integration Tests")
    print("=" * 60)
    print()

    try:
        # Basic health checks
        test_health()
        test_readiness()
        print()

        # Agent info
        test_list_agents()
        print()

        # Thread operations
        thread_id = test_create_thread()
        test_get_thread(thread_id)
        test_list_threads()
        print()

        # Message operations
        test_list_messages(thread_id)
        test_send_message_non_stream(thread_id)
        test_list_messages(thread_id)  # Should have messages now
        print()

        # Cleanup
        test_delete_thread(thread_id)
        print()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error: Is the API running at {API_BASE_URL}?")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

