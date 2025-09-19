import requests
import sys
import json
from datetime import datetime

class MindfulMateAPITester:
    def __init__(self, base_url="https://moodpal-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_status_endpoints(self):
        """Test status check endpoints"""
        # Test creating a status check
        success, response = self.run_test(
            "Create Status Check",
            "POST",
            "status",
            200,
            data={"client_name": "test_client"}
        )
        
        if success:
            # Test getting status checks
            self.run_test("Get Status Checks", "GET", "status", 200)
        
        return success

    def test_chat_functionality(self):
        """Test the main chat functionality"""
        # Test sending a chat message (new session)
        success, response = self.run_test(
            "Send Chat Message (New Session)",
            "POST",
            "chat",
            200,
            data={"message": "Hello, I'm feeling anxious today"}
        )
        
        if success and 'session_id' in response:
            self.session_id = response['session_id']
            print(f"   Session ID: {self.session_id}")
            
            # Test sending another message in the same session
            success2, response2 = self.run_test(
                "Send Chat Message (Existing Session)",
                "POST",
                "chat",
                200,
                data={
                    "message": "Can you help me with breathing exercises?",
                    "session_id": self.session_id
                }
            )
            
            if success2:
                # Test getting chat history
                self.run_test(
                    "Get Chat History",
                    "GET",
                    f"chat/history/{self.session_id}",
                    200
                )
                
                # Test getting chat sessions
                self.run_test(
                    "Get Chat Sessions",
                    "GET",
                    "chat/sessions",
                    200
                )
        
        return success

    def test_chat_edge_cases(self):
        """Test edge cases for chat functionality"""
        # Test empty message
        success1, _ = self.run_test(
            "Send Empty Message",
            "POST",
            "chat",
            422,  # Should return validation error
            data={"message": ""}
        )
        
        # Test invalid session ID
        success2, _ = self.run_test(
            "Get History with Invalid Session",
            "GET",
            "chat/history/invalid-session-id",
            200  # Should return empty array or handle gracefully
        )
        
        return True  # Edge cases are informational

    def test_wellness_responses(self):
        """Test that responses are wellness-focused"""
        test_messages = [
            "I'm feeling stressed",
            "I need help with anxiety",
            "How can I feel better?",
            "I'm having a bad day"
        ]
        
        wellness_keywords = [
            'feel', 'stress', 'anxiety', 'breath', 'support', 'help',
            'wellness', 'mental', 'care', 'better', 'exercise', 'mindful'
        ]
        
        wellness_responses = 0
        
        for message in test_messages:
            success, response = self.run_test(
                f"Wellness Response Test: '{message[:20]}...'",
                "POST",
                "chat",
                200,
                data={"message": message}
            )
            
            if success and 'message' in response:
                response_text = response['message'].lower()
                if any(keyword in response_text for keyword in wellness_keywords):
                    wellness_responses += 1
                    print(f"   ✅ Response contains wellness keywords")
                else:
                    print(f"   ⚠️  Response may not be wellness-focused")
        
        print(f"\n📊 Wellness-focused responses: {wellness_responses}/{len(test_messages)}")
        return wellness_responses > 0

def main():
    print("🧠 MindfulMate API Testing Suite")
    print("=" * 50)
    
    # Setup
    tester = MindfulMateAPITester()
    
    # Run all tests
    print("\n🔧 Testing Basic Endpoints...")
    tester.test_root_endpoint()
    tester.test_status_endpoints()
    
    print("\n💬 Testing Chat Functionality...")
    tester.test_chat_functionality()
    
    print("\n🔍 Testing Edge Cases...")
    tester.test_chat_edge_cases()
    
    print("\n🌱 Testing Wellness Focus...")
    tester.test_wellness_responses()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())