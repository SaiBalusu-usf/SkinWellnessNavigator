#!/usr/bin/env python3
"""
Test runner script for Skin Wellness Navigator.
Executes tests and generates coverage reports.
"""

import os
import sys
import pytest
import coverage
import argparse
from datetime import datetime

def setup_test_environment():
    """Set up the test environment."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    
    # Create necessary directories
    directories = ['logs', 'coverage_reports', 'test_results']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def run_tests(args):
    """Run the test suite with specified options."""
    # Initialize coverage
    cov = coverage.Coverage(
        config_file='.coveragerc',
        source=['.'],
        omit=[
            'tests/*',
            'venv/*',
            'run_tests.py'
        ]
    )
    
    # Start coverage collection
    cov.start()
    
    try:
        # Build pytest arguments
        pytest_args = [
            '--verbose',
            '--showlocals',
            f'--junitxml=test_results/junit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml'
        ]
        
        # Add coverage options
        pytest_args.extend([
            '--cov=.',
            '--cov-report=term-missing',
            f'--cov-report=html:coverage_reports/html_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        ])
        
        # Add user-specified arguments
        if args.markers:
            pytest_args.extend(['-m', args.markers])
        
        if args.failfast:
            pytest_args.append('--exitfirst')
        
        if args.verbose:
            pytest_args.append('-vv')
        
        # Run tests
        result = pytest.main(pytest_args)
        
        # Stop coverage collection
        cov.stop()
        cov.save()
        
        # Generate coverage reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cov.xml_report(outfile=f'coverage_reports/coverage_{timestamp}.xml')
        cov.json_report(outfile=f'coverage_reports/coverage_{timestamp}.json')
        
        return result
        
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        return 1

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run tests for Skin Wellness Navigator'
    )
    
    parser.add_argument(
        '--markers',
        help='Only run tests with specific markers (e.g., "unit" or "integration")'
    )
    
    parser.add_argument(
        '--failfast',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    try:
        setup_test_environment()
        
        print("Starting test run...")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        result = run_tests(args)
        
        print("=" * 80)
        print(f"Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if result == 0:
            print("\nAll tests passed successfully!")
            sys.exit(0)
        else:
            print("\nSome tests failed or errors occurred.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest run interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nError during test execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
