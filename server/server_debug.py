# server_debug.py - Test your server directly
import requests
import json

SERVER_URL = "http://127.0.0.1:5000"

def test_server_health():
    """Test if server is responding"""
    try:
        response = requests.get(f"{SERVER_URL}/")
        print(f"✅ Server health: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Server health failed: {e}")
        return False

def test_conversation_state():
    """Test conversation state endpoint"""
    try:
        response = requests.get(f"{SERVER_URL}/get_conversation_state")
        print(f"✅ Conversation state: {response.status_code}")
        data = response.json()
        print(f"   Phase: {data.get('phase')}")
        print(f"   ML Output Exists: {data.get('ml_output_exists')}")
        print(f"   Phase2 Activated: {data.get('phase2_activated')}")
        return True
    except Exception as e:
        print(f"❌ Conversation state failed: {e}")
        return False

def test_llm_message():
    """Test the main message endpoint"""
    try:
        test_message = "what is the embodied carbon"
        response = requests.post(
            f"{SERVER_URL}/llm_message",
            json={"message": test_message},
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ LLM Message: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Phase: {data.get('phase')}")
            print(f"   Response: {data.get('response', '')[:100]}...")
            print(f"   Error: {data.get('error')}")
        else:
            print(f"   Error: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ LLM Message failed: {e}")
        return False

def test_initial_greeting():
    """Test initial greeting endpoint"""
    try:
        response = requests.get(f"{SERVER_URL}/get_initial_greeting")
        print(f"✅ Initial greeting: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('response', '')[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Initial greeting failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Server Endpoints...")
    print("=" * 50)
    
    # Test all endpoints
    health_ok = test_server_health()
    print()
    
    if health_ok:
        test_conversation_state()
        print()
        
        test_initial_greeting()
        print()
        
        test_llm_message()
        print()
    
    print("🏁 Testing complete!")
    
    if not health_ok:
        print("\n💡 Suggestions:")
        print("1. Make sure server is running: python main_llm1.py")
        print("2. Check server terminal for errors")
        print("3. Try restarting the server")