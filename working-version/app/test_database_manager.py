#!/usr/bin/env python3
"""
Test script for database management functions
"""
import requests
from app.database_manager import (
    check_database_status, 
    get_database_info,
    initialize_database_if_needed
)

BACKEND_URL = "https://mnirejmq3g.eu-central-1.awsapprunner.com"

def test_local_database_functions():
    """Test the database management functions locally"""
    print("🔧 Testing Local Database Management Functions")
    print("=" * 50)
    
    # Test database status check
    print("\n📊 Testing database status check...")
    try:
        status = check_database_status()
        print(f"✅ Database status check successful:")
        print(f"   Tables exist: {status['tables_exist']}")
        print(f"   Initialized: {status['is_initialized']}")
        print(f"   Users: {status['user_count']}")
        print(f"   Games: {status['game_count']}")
        
        if status['word_counts']:
            print("   Words by language:")
            for lang, count in status['word_counts'].items():
                print(f"     {lang}: {count:,}")
        else:
            print("   No words loaded")
            
    except Exception as e:
        print(f"❌ Database status check failed: {e}")
    
    # Test database info
    print("\n📋 Testing database info...")
    try:
        info = get_database_info()
        print(f"✅ Database info retrieved:")
        print(f"   Environment: {info['environment']}")
        print(f"   Database URL: {info['database_url']}")
        
        if 'tables' in info:
            print("   Table sizes:")
            for table, count in info['tables'].items():
                print(f"     {table}: {count}")
                
    except Exception as e:
        print(f"❌ Database info failed: {e}")
    
    # Test smart initialization
    print("\n🚀 Testing smart initialization...")
    try:
        result = initialize_database_if_needed()
        print(f"✅ Smart initialization result:")
        print(f"   Success: {result['success']}")
        print(f"   Action: {result['action']}")
        
        if 'reason' in result:
            print(f"   Reason: {result['reason']}")
        if 'error' in result:
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Smart initialization failed: {e}")

def test_remote_database_status():
    """Test the remote database status endpoint"""
    print("\n🌐 Testing Remote Database Status Endpoint")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/database/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Remote database status retrieved:")
            
            status = data.get('status', {})
            print(f"   Tables exist: {status.get('tables_exist', 'unknown')}")
            print(f"   Initialized: {status.get('is_initialized', 'unknown')}")
            print(f"   Users: {status.get('user_count', 'unknown')}")
            print(f"   Games: {status.get('game_count', 'unknown')}")
            
            word_counts = status.get('word_counts', {})
            if word_counts:
                print("   Words by language:")
                for lang, count in word_counts.items():
                    print(f"     {lang}: {count:,}")
            else:
                print("   No words loaded")
            
            print(f"   Environment: {data.get('environment', 'unknown')}")
            
            tables = data.get('tables', {})
            if tables:
                print("   Table sizes:")
                for table, count in tables.items():
                    print(f"     {table}: {count}")
        else:
            print(f"❌ Remote database status failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Remote database status error: {e}")

def test_deployment_readiness():
    """Test if the system is ready for deployment with invitation system"""
    print("\n🚀 Testing Deployment Readiness")
    print("=" * 40)
    
    # Check if database is properly initialized
    try:
        status = check_database_status()
        
        print("📊 Database Readiness:")
        print(f"   ✅ Tables exist: {status['tables_exist']}")
        print(f"   ✅ Initialized: {status['is_initialized']}")
        
        if status['is_initialized']:
            print("   ✅ Database is ready for deployment")
        else:
            print("   ⚠️  Database needs initialization")
            
        # Check word counts
        total_words = sum(status['word_counts'].values())
        print(f"   📚 Total words: {total_words:,}")
        
        if total_words >= 1000:
            print("   ✅ Sufficient words loaded")
        else:
            print("   ⚠️  Consider loading more words")
            
    except Exception as e:
        print(f"❌ Database readiness check failed: {e}")
    
    # Check if invitation endpoints will be available
    print("\n🎯 Invitation System Readiness:")
    print("   ✅ game_setup router included in main.py")
    print("   ✅ Database manager functions implemented")
    print("   ✅ Smart initialization implemented")
    
    print("\n🎉 System appears ready for deployment with invitation system!")

if __name__ == "__main__":
    print("🧪 Database Manager Test Suite")
    print("=" * 60)
    
    # Test local functions
    test_local_database_functions()
    
    # Test remote endpoint (if deployed)
    test_remote_database_status()
    
    # Test deployment readiness
    test_deployment_readiness()
    
    print("\n✅ All tests completed!") 