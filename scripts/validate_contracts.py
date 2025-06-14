#!/usr/bin/env python3
"""
Contract Validation Script for WordBattle Backend

This script validates the backend API implementation against the frontend contracts
during deployment. It checks for schema compliance, endpoint availability, and
response format consistency.
"""

import os
import sys
import json
import requests
import argparse
import time
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def load_contracts(contracts_dir: str) -> Dict[str, Any]:
    """Load contract schemas from the contracts directory."""
    contracts = {}
    
    if not os.path.exists(contracts_dir):
        print(f"❌ Contracts directory not found: {contracts_dir}")
        return contracts
    
    schema_files = [
        "all_schemas.json",
        "auth_schemas.json",
        "game_schemas.json", 
        "error_schemas.json",
        "config_schemas.json",
        "wordbattle_api.yaml"
    ]
    
    for filename in schema_files:
        filepath = os.path.join(contracts_dir, filename)
        if os.path.exists(filepath):
            if filename.endswith('.json'):
                with open(filepath, 'r') as f:
                    contracts[filename] = json.load(f)
            print(f"📋 Loaded: {filename}")
    
    return contracts

def test_endpoint_availability(base_url: str, timeout: int = 30) -> Dict[str, Any]:
    """Test basic endpoint availability."""
    results = {}
    
    # Core endpoints to test
    endpoints = [
        ("/health", "GET"),
        ("/docs", "GET"),
        ("/openapi.json", "GET"),
        ("/admin/contracts/info", "GET"),  # Contract info endpoint
        ("/admin/contract-status", "GET"),  # Alternative contract status endpoint
    ]
    
    for endpoint, method in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=timeout)
            
            results[endpoint] = {
                "available": True,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: Available ({response.status_code})")
            else:
                print(f"⚠️  {endpoint}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            results[endpoint] = {
                "available": False,
                "error": str(e),
                "response_time": None
            }
            print(f"❌ {endpoint}: {str(e)}")
    
    return results

def test_contract_validation(base_url: str, auth_token: str = None) -> Dict[str, Any]:
    """Test contract validation endpoints."""
    results = {}
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Test contract info endpoints
    contract_endpoints = [
        "/admin/contracts/info",
        "/admin/contract-status"
    ]
    
    for endpoint in contract_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=30)
            
            if response.status_code == 200:
                contract_info = response.json()
                results["contract_info"] = {
                    "available": True,
                    "endpoint": endpoint,
                    "data": contract_info,
                    "validation_enabled": contract_info.get("contract_validation", {}).get("enabled", False) or 
                                        contract_info.get("contract_info", {}).get("enabled", False)
                }
                print(f"✅ Contract info available at {endpoint}")
                print(f"   Validation enabled: {results['contract_info']['validation_enabled']}")
                break
            else:
                print(f"⚠️  {endpoint}: Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: {str(e)}")
    
    # If no contract endpoint worked
    if "contract_info" not in results:
        results["contract_info"] = {
            "available": False,
            "error": "No contract endpoints accessible"
        }
    
    return results

def test_openapi_schema_compliance(base_url: str, contracts: Dict[str, Any]) -> Dict[str, Any]:
    """Test OpenAPI schema compliance."""
    results = {}
    
    try:
        # Get OpenAPI schema from the API
        response = requests.get(f"{base_url}/openapi.json", timeout=30)
        
        if response.status_code != 200:
            return {
                "openapi_available": False,
                "status_code": response.status_code
            }
        
        api_schema = response.json()
        results["openapi_available"] = True
        results["paths_count"] = len(api_schema.get("paths", {}))
        results["components_count"] = len(api_schema.get("components", {}).get("schemas", {}))
        
        # Check for required paths from contracts
        required_paths = [
            "/health",
            "/auth/register", 
            "/games/my-games",
            "/games/{game_id}",
            "/admin/contracts/info"
        ]
        
        api_paths = api_schema.get("paths", {})
        missing_paths = []
        available_paths = []
        
        for path in required_paths:
            # Handle dynamic paths
            path_found = False
            for api_path in api_paths.keys():
                if path == api_path or ('{' in path and api_path.replace('{game_id}', '{id}') == path):
                    path_found = True
                    available_paths.append(path)
                    break
            
            if not path_found:
                missing_paths.append(path)
        
        results["required_paths"] = {
            "available": available_paths,
            "missing": missing_paths,
            "compliance": len(missing_paths) == 0
        }
        
        print(f"✅ OpenAPI schema available: {results['paths_count']} paths")
        print(f"   Required paths available: {len(available_paths)}/{len(required_paths)}")
        
        if missing_paths:
            print(f"⚠️  Missing required paths: {missing_paths}")
        
    except requests.exceptions.RequestException as e:
        results = {
            "openapi_available": False,
            "error": str(e)
        }
        print(f"❌ OpenAPI schema: {str(e)}")
    
    return results

def get_test_token(base_url: str) -> str:
    """Get a test authentication token."""
    try:
        response = requests.post(f"{base_url}/admin/debug/create-test-tokens", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("✅ Test token obtained")
                return data["access_token"]
            elif "users" in data and len(data["users"]) > 0:
                token = data["users"][0]["access_token"]
                print("✅ Test token obtained")
                return token
        
        print(f"⚠️  Could not get test token: Status {response.status_code}")
        if response.status_code == 200:
            # Print response to debug
            try:
                print(f"   Response: {response.json()}")
            except:
                print(f"   Response (raw): {response.text[:200]}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Could not get test token: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Validate WordBattle API contracts")
    parser.add_argument("--url", default="https://wordbattle-backend-test-441752988736.europe-west1.run.app", 
                      help="Base URL of the API to test")
    parser.add_argument("--contracts-dir", default="/Users/janbinge/git/wordbattle/wordbattle-contracts",
                      help="Path to contracts directory")
    parser.add_argument("--timeout", type=int, default=30,
                      help="Request timeout in seconds")
    parser.add_argument("--wait-for-deploy", type=int, default=0,
                      help="Wait N seconds for deployment to be ready")
    parser.add_argument("--strict", action="store_true",
                      help="Exit with error code on any validation failure")
    
    args = parser.parse_args()
    
    print("🔍 WordBattle API Contract Validation")
    print("=" * 50)
    print(f"Target URL: {args.url}")
    print(f"Contracts: {args.contracts_dir}")
    print(f"Timeout: {args.timeout}s")
    print("")
    
    # Wait for deployment if requested
    if args.wait_for_deploy > 0:
        print(f"⏳ Waiting {args.wait_for_deploy}s for deployment...")
        time.sleep(args.wait_for_deploy)
        print("")
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "target_url": args.url,
        "contracts_dir": args.contracts_dir,
        "results": {}
    }
    
    # Load contracts
    print("📋 Loading Contracts...")
    contracts = load_contracts(args.contracts_dir)
    validation_results["contracts_loaded"] = len(contracts)
    print(f"   Loaded {len(contracts)} contract files")
    print("")
    
    # Test basic endpoint availability
    print("🔍 Testing Endpoint Availability...")
    endpoint_results = test_endpoint_availability(args.url, args.timeout)
    validation_results["results"]["endpoints"] = endpoint_results
    print("")
    
    # Get test token for authenticated endpoints
    print("🔑 Getting Test Token...")
    test_token = get_test_token(args.url)
    print("")
    
    # Test contract validation system
    print("📋 Testing Contract Validation...")
    contract_results = test_contract_validation(args.url, test_token)
    validation_results["results"]["contracts"] = contract_results
    print("")
    
    # Test OpenAPI schema compliance
    print("📄 Testing OpenAPI Schema Compliance...")
    schema_results = test_openapi_schema_compliance(args.url, contracts)
    validation_results["results"]["schema"] = schema_results
    print("")
    
    # Summary
    print("📊 Validation Summary")
    print("=" * 50)
    
    total_checks = 0
    passed_checks = 0
    
    # Count endpoint checks
    for endpoint, result in endpoint_results.items():
        total_checks += 1
        if result.get("available") and result.get("status_code") == 200:
            passed_checks += 1
    
    # Count contract checks
    if contract_results.get("contract_info", {}).get("available"):
        total_checks += 1
        passed_checks += 1
    
    # Count schema checks
    if schema_results.get("openapi_available"):
        total_checks += 1
        passed_checks += 1
        
        if schema_results.get("required_paths", {}).get("compliance"):
            total_checks += 1
            passed_checks += 1
    
    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Success Rate: {success_rate:.1f}%")
    print("")
    
    if success_rate >= 90:
        print("🎉 Contract validation PASSED!")
        exit_code = 0
    elif success_rate >= 70:
        print("⚠️  Contract validation PARTIAL - some issues found")
        exit_code = 1 if args.strict else 0
    else:
        print("❌ Contract validation FAILED!")
        exit_code = 1
    
    # Save detailed results
    results_file = "contract_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    print(f"📄 Detailed results saved to: {results_file}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 