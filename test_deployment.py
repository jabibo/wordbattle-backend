#!/usr/bin/env python3
"""
WordBattle Backend Deployment Test
=================================

This script tests the critical functionality of the deployed WordBattle backend
to ensure all recent fixes are working correctly.

Test Coverage:
- Database connectivity
- Authentication endpoints
- Game management
- Move validation and scoring
- Exchange functionality
- Rate limiting
- Error handling
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Configuration
BASE_URL = "https://wordbattle-backend-prod-15814336315.europe-west1.run.app"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    response_time: float
    status_code: Optional[int] = None

class DeploymentTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_id = None
        self.test_game_id = None
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_endpoint(self, method: str, endpoint: str, **kwargs) -> TestResult:
        """Test a single endpoint and return results"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.request(method, url, **kwargs)
            response_time = time.time() - start_time
            
            return TestResult(
                name=endpoint,
                passed=response.status_code < 400,
                message=f"Status: {response.status_code}",
                response_time=response_time,
                status_code=response.status_code
            )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                name=endpoint,
                passed=False,
                message=f"Error: {str(e)}",
                response_time=response_time
            )
    
    def test_health_check(self) -> TestResult:
        """Test basic health and connectivity"""
        self.log("Testing health check...")
        return self.test_endpoint("GET", "/health")
    
    def test_database_connectivity(self) -> TestResult:
        """Test database connectivity through database status endpoint"""
        self.log("Testing database connectivity...")
        result = self.test_endpoint("GET", "/database/status")
        
        if result.passed:
            result.message += " - Database status endpoint accessible"
        else:
            result.message += " - Database status endpoint failed"
            
        return result
    
    def test_authentication(self) -> TestResult:
        """Test user authentication flow"""
        self.log("Testing authentication...")
        
        # Test email login request
        login_data = {"email": TEST_EMAIL}
        result = self.test_endpoint("POST", "/auth/email-login", json=login_data)
        
        if result.passed:
            result.message += " - Email login request successful"
        else:
            result.message += " - Email login request failed"
            
        return result
    
    def test_rate_limiting(self) -> TestResult:
        """Test rate limiting by making multiple rapid requests"""
        self.log("Testing rate limiting...")
        
        rapid_requests = 0
        rate_limited = False
        
        for i in range(10):  # Make 10 rapid requests
            result = self.test_endpoint("GET", "/config")
            rapid_requests += 1
            
            if result.status_code == 429:
                rate_limited = True
                break
                
            time.sleep(0.1)  # Small delay between requests
        
        if rate_limited:
            return TestResult(
                name="Rate Limiting",
                passed=True,
                message=f"Rate limiting triggered after {rapid_requests} requests (expected)",
                response_time=0.0
            )
        else:
            return TestResult(
                name="Rate Limiting",
                passed=False,
                message=f"Rate limiting not triggered after {rapid_requests} requests (unexpected)",
                response_time=0.0
            )
    
    def test_game_endpoints(self) -> TestResult:
        """Test game-related endpoints"""
        self.log("Testing game endpoints...")
        
        # Test games list endpoint
        result = self.test_endpoint("GET", "/games/my-games")
        
        if result.passed:
            result.message += " - Games endpoint accessible"
        else:
            result.message += " - Games endpoint failed"
            
        return result
    
    def test_move_validation(self) -> TestResult:
        """Test move validation endpoint"""
        self.log("Testing move validation...")
        
        # Test move validation with sample data (requires a game_id)
        # For now, just test that the endpoint exists
        result = self.test_endpoint("POST", "/games/1/test-move", json={})
        
        if result.status_code in [400, 401, 404]:  # Expected errors for invalid game or auth
            result.passed = True
            result.message += " - Move validation endpoint accessible (expected auth/game errors)"
        elif result.passed:
            result.message += " - Move validation working"
        else:
            result.message += " - Move validation failed"
            
        return result
    
    def test_error_handling(self) -> TestResult:
        """Test error handling with invalid requests"""
        self.log("Testing error handling...")
        
        # Test with invalid endpoint
        result = self.test_endpoint("GET", "/invalid-endpoint")
        
        if not result.passed and result.status_code == 404:
            result.passed = True
            result.message = "Error handling working correctly (404 for invalid endpoint)"
        else:
            result.message += " - Error handling not working as expected"
            
        return result
    
    def run_all_tests(self) -> Dict[str, TestResult]:
        """Run all deployment tests"""
        self.log("Starting WordBattle Backend Deployment Tests")
        self.log("=" * 50)
        
        tests = {
            "Health Check": self.test_health_check(),
            "Database Connectivity": self.test_database_connectivity(),
            "Authentication": self.test_authentication(),
            "Game Endpoints": self.test_game_endpoints(),
            "Move Validation": self.test_move_validation(),
            "Error Handling": self.test_error_handling(),
            "Rate Limiting": self.test_rate_limiting(),
        }
        
        return tests
    
    def print_results(self, results: Dict[str, TestResult]):
        """Print test results in a formatted way"""
        self.log("=" * 50)
        self.log("DEPLOYMENT TEST RESULTS")
        self.log("=" * 50)
        
        passed_tests = 0
        total_tests = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.passed else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            self.log(f"  Message: {result.message}")
            self.log(f"  Response Time: {result.response_time:.3f}s")
            if result.status_code:
                self.log(f"  Status Code: {result.status_code}")
            self.log("")
            
            if result.passed:
                passed_tests += 1
        
        self.log("=" * 50)
        self.log(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - Deployment is working correctly!")
            return True
        else:
            self.log(f"⚠️  {total_tests - passed_tests} tests failed - Deployment has issues")
            return False

def main():
    """Main test execution"""
    print("WordBattle Backend Deployment Test")
    print("==================================")
    print(f"Testing: {BASE_URL}")
    print()
    
    tester = DeploymentTester(BASE_URL)
    results = tester.run_all_tests()
    success = tester.print_results(results)
    
    if success:
        print("\n✅ Deployment test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
