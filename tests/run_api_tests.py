#!/usr/bin/env python3
"""
Test runner for WordBattle API test suite.
Provides convenient ways to run the comprehensive API tests.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle output."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run WordBattle API tests")
    parser.add_argument(
        "--test-type", 
        choices=["all", "auth", "users", "games", "moves", "admin", "comprehensive"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true", 
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--markers", "-m",
        help="Run tests with specific markers"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test files based on type
    test_files = {
        "auth": ["tests/test_auth_api.py"],
        "users": ["tests/test_users_api.py"],
        "games": ["tests/test_games_api.py"],
        "moves": ["tests/test_moves_rack_api.py"],
        "admin": ["tests/test_admin_api.py"],
        "comprehensive": ["tests/test_comprehensive_api.py"],
        "all": [
            "tests/test_auth_api.py",
            "tests/test_users_api.py", 
            "tests/test_games_api.py",
            "tests/test_moves_rack_api.py",
            "tests/test_admin_api.py",
            "tests/test_comprehensive_api.py"
        ]
    }
    
    # Add test files to command
    if args.test_type in test_files:
        cmd.extend(test_files[args.test_type])
    else:
        cmd.append("tests/")
    
    # Add options
    if args.verbose:
        cmd.append("-v")
    
    if args.fail_fast:
        cmd.append("-x")
        
    if args.parallel:
        cmd.extend(["-n", "auto"])
        
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    # Coverage options
    if args.coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=term-missing"
        ])
        
        if args.html_report:
            cmd.extend(["--cov-report=html:htmlcov"])
    
    # Environment setup
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)
    
    # Run the tests
    success = run_command(cmd, f"API Tests ({args.test_type})")
    
    if args.coverage and args.html_report:
        print(f"\n{'='*60}")
        print("Coverage report generated in htmlcov/index.html")
        print(f"{'='*60}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 