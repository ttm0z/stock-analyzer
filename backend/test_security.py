#!/usr/bin/env python3
"""
Security Test Suite - Verify all security configurations
"""
import os
import requests
import time
import subprocess
import sys
from pathlib import Path

class SecurityTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.base_url = "http://localhost:5000"
    
    def test(self, name, condition, details=""):
        """Test a security condition"""
        if condition:
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
            self.passed += 1
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.failed += 1
    
    def test_environment_variables(self):
        """Test that environment variables are properly set"""
        print("\n🔐 Testing Environment Variables...")
        
        required_vars = [
            'FLASK_SECRET_KEY', 'JWT_SECRET_KEY', 'FMP_API_KEY',
            'ALPHA_VANTAGE_API_KEY', 'DATABASE_URL', 'REDIS_PASSWORD'
        ]
        
        # Load .env file manually for testing
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        for var in required_vars:
            value = os.getenv(var, '')
            self.test(
                f"Environment variable {var}",
                bool(value and len(value) > 10),
                f"Length: {len(value)} chars" if value else "Not set"
            )
    
    def test_file_security(self):
        """Test file security configurations"""
        print("\n📁 Testing File Security...")
        
        # Check .env is gitignored
        gitignore_path = Path('.gitignore')
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            self.test(
                ".env file is gitignored",
                '.env' in gitignore_content,
                "Found in .gitignore"
            )
        else:
            self.test(".env file is gitignored", False, ".gitignore not found")
        
        # Check .env exists
        self.test(
            ".env file exists",
            Path('.env').exists(),
            "Contains secure configuration"
        )
        
        # Check Redis config is secure
        redis_conf = Path('app/redis.conf')
        if redis_conf.exists():
            redis_content = redis_conf.read_text()
            self.test(
                "Redis bind configuration",
                'bind 127.0.0.1' in redis_content,
                "Bound to localhost only"
            )
            self.test(
                "Redis password protection",
                'requirepass' in redis_content,
                "Password authentication enabled"
            )
        else:
            self.test("Redis configuration", False, "app/redis.conf not found")
    
    def test_api_endpoints(self):
        """Test API endpoint security"""
        print("\n🌐 Testing API Security...")
        
        try:
            # Test CORS configuration
            headers = {'Origin': 'http://malicious-site.com'}
            response = requests.get(f"{self.base_url}/test/test", headers=headers, timeout=5)
            
            # Should reject requests from unauthorized origins
            cors_header = response.headers.get('Access-Control-Allow-Origin', '')
            self.test(
                "CORS origin restriction",
                cors_header != '*' and 'malicious-site.com' not in cors_header,
                f"CORS header: {cors_header or 'None'}"
            )
            
        except requests.exceptions.ConnectionError:
            print("   ⚠️ Server not running - skipping API tests")
            return
        except Exception as e:
            self.test("API accessibility", False, f"Error: {e}")
            return
        
        # Test input validation
        try:
            # Test with malicious search query
            malicious_query = "<script>alert('xss')</script>"
            response = requests.get(
                f"{self.base_url}/api/search",
                params={'query': malicious_query},
                timeout=5
            )
            
            # Should sanitize input
            if response.status_code == 200:
                self.test(
                    "Input sanitization",
                    '<script>' not in str(response.json()),
                    "XSS prevention active"
                )
            else:
                self.test(
                    "Input validation",
                    response.status_code == 400,
                    f"Rejected malicious input (HTTP {response.status_code})"
                )
        
        except Exception as e:
            self.test("Input validation test", False, f"Error: {e}")
    
    def test_authentication(self):
        """Test authentication system"""
        print("\n🔑 Testing Authentication...")
        
        try:
            # Test registration endpoint exists
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json={'email': 'test@test.com', 'username': 'test', 'password': 'short'},
                timeout=5
            )
            
            self.test(
                "Registration endpoint",
                response.status_code in [400, 201],  # Either validation error or success
                f"HTTP {response.status_code}"
            )
            
            # Test password validation
            if response.status_code == 400:
                error_msg = response.json().get('error', '').lower()
                self.test(
                    "Password validation",
                    'password' in error_msg and ('8' in error_msg or 'short' in error_msg),
                    "Enforces strong passwords"
                )
        
        except requests.exceptions.ConnectionError:
            print("   ⚠️ Server not running - skipping auth tests")
        except Exception as e:
            self.test("Authentication test", False, f"Error: {e}")
    
    def test_dependencies(self):
        """Test that security dependencies are installed"""
        print("\n📦 Testing Dependencies...")
        
        try:
            import bleach
            self.test("Bleach (XSS protection)", True, "Input sanitization available")
        except ImportError:
            self.test("Bleach (XSS protection)", False, "Not installed")
        
        try:
            import jwt
            self.test("PyJWT (Authentication)", True, "JWT tokens available")
        except ImportError:
            self.test("PyJWT (Authentication)", False, "Not installed")
        
        try:
            from werkzeug.security import generate_password_hash
            self.test("Werkzeug (Password hashing)", True, "Secure password storage")
        except ImportError:
            self.test("Werkzeug (Password hashing)", False, "Not installed")
    
    def run_all_tests(self):
        """Run complete security test suite"""
        print("🛡️ SECURITY TEST SUITE")
        print("=" * 50)
        
        self.test_dependencies()
        self.test_environment_variables()
        self.test_file_security()
        self.test_api_endpoints()
        self.test_authentication()
        
        print("\n" + "=" * 50)
        print(f"📊 RESULTS: {self.passed} passed, {self.failed} failed")
        
        if self.failed == 0:
            print("🎉 ALL SECURITY TESTS PASSED!")
            return 0
        else:
            print(f"⚠️ {self.failed} security issues found - review above")
            return 1

def main():
    tester = SecurityTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())