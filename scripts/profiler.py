#!/usr/bin/env python3
"""
Performance profiling script for Skin Wellness Navigator.
Analyzes code performance, identifies bottlenecks, and suggests optimizations.
"""

import os
import sys
import cProfile
import pstats
import io
import time
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import functools
import tracemalloc
import json
import requests
from line_profiler import LineProfiler
import memory_profiler
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/profiler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """Handles performance profiling and analysis."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.profile_dir = self.project_root / 'profiles'
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tracemalloc for memory tracking
        tracemalloc.start()

    def profile_function(self, func: Callable, *args, **kwargs) -> Dict:
        """
        Profile a function's execution.
        
        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Dict: Profiling results
        """
        # CPU profiling
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Memory tracking
        tracemalloc.start()
        start_mem = tracemalloc.get_traced_memory()
        
        # Time tracking
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.time()
            end_mem = tracemalloc.get_traced_memory()
            profiler.disable()
            
            # Get CPU stats
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats()
            
            # Calculate memory usage
            mem_diff = end_mem[0] - start_mem[0]
            peak_mem = end_mem[1]
            
            profile_data = {
                'timestamp': datetime.now().isoformat(),
                'function': func.__name__,
                'execution_time': end_time - start_time,
                'memory_used': mem_diff,
                'peak_memory': peak_mem,
                'cpu_profile': s.getvalue(),
                'success': True
            }
            
            # Save profile data
            self._save_profile(profile_data)
            
            return profile_data

    def profile_api_endpoint(self, url: str, method: str = 'GET', **kwargs) -> Dict:
        """
        Profile API endpoint performance.
        
        Args:
            url: API endpoint URL
            method: HTTP method
            **kwargs: Additional request parameters
            
        Returns:
            Dict: Profiling results
        """
        start_time = time.time()
        
        try:
            response = requests.request(method, url, **kwargs)
            end_time = time.time()
            
            profile_data = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'method': method,
                'response_time': end_time - start_time,
                'status_code': response.status_code,
                'response_size': len(response.content),
                'success': response.ok
            }
            
            # Save profile data
            self._save_profile(profile_data)
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error profiling API endpoint: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'method': method,
                'error': str(e),
                'success': False
            }

    def _save_profile(self, profile_data: Dict):
        """Save profile data to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_file = self.profile_dir / f"profile_{timestamp}.json"
        
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)

    def analyze_profiles(self, time_range: Optional[int] = None) -> Dict:
        """
        Analyze saved profile data.
        
        Args:
            time_range: Optional time range in hours
            
        Returns:
            Dict: Analysis results
        """
        profiles = []
        
        # Load profiles
        for profile_file in self.profile_dir.glob("*.json"):
            try:
                with open(profile_file) as f:
                    profile = json.load(f)
                    
                if time_range:
                    profile_time = datetime.fromisoformat(profile['timestamp'])
                    age = (datetime.now() - profile_time).total_seconds() / 3600
                    if age > time_range:
                        continue
                        
                profiles.append(profile)
                
            except Exception as e:
                logger.error(f"Error reading profile {profile_file}: {e}")
        
        if not profiles:
            return {}
        
        # Analyze function profiles
        function_stats = {}
        for profile in profiles:
            if 'function' in profile:
                func_name = profile['function']
                if func_name not in function_stats:
                    function_stats[func_name] = {
                        'calls': 0,
                        'total_time': 0,
                        'avg_time': 0,
                        'total_memory': 0,
                        'avg_memory': 0,
                        'success_rate': 0
                    }
                
                stats = function_stats[func_name]
                stats['calls'] += 1
                stats['total_time'] += profile['execution_time']
                stats['total_memory'] += profile.get('memory_used', 0)
                stats['success_rate'] += 1 if profile['success'] else 0
        
        # Calculate averages
        for stats in function_stats.values():
            stats['avg_time'] = stats['total_time'] / stats['calls']
            stats['avg_memory'] = stats['total_memory'] / stats['calls']
            stats['success_rate'] = (stats['success_rate'] / stats['calls']) * 100
        
        # Analyze API profiles
        api_stats = {}
        for profile in profiles:
            if 'url' in profile:
                endpoint = f"{profile['method']} {profile['url']}"
                if endpoint not in api_stats:
                    api_stats[endpoint] = {
                        'calls': 0,
                        'total_time': 0,
                        'avg_time': 0,
                        'success_rate': 0
                    }
                
                stats = api_stats[endpoint]
                stats['calls'] += 1
                stats['total_time'] += profile['response_time']
                stats['success_rate'] += 1 if profile['success'] else 0
        
        # Calculate API averages
        for stats in api_stats.values():
            stats['avg_time'] = stats['total_time'] / stats['calls']
            stats['success_rate'] = (stats['success_rate'] / stats['calls']) * 100
        
        return {
            'function_stats': function_stats,
            'api_stats': api_stats,
            'total_profiles': len(profiles)
        }

    def get_system_metrics(self) -> Dict:
        """
        Get current system performance metrics.
        
        Returns:
            Dict: System metrics
        """
        cpu = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'overall': sum(cpu) / len(cpu),
                'per_cpu': cpu
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        }

def profile_decorator(func):
    """Decorator to profile function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = PerformanceProfiler()
        return profiler.profile_function(func, *args, **kwargs)
    return wrapper

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance profiling tool")
    
    parser.add_argument(
        'action',
        choices=['analyze', 'system'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--time-range',
        type=int,
        help='Time range in hours for analysis'
    )
    
    args = parser.parse_args()
    
    profiler = PerformanceProfiler()
    
    try:
        if args.action == 'analyze':
            results = profiler.analyze_profiles(args.time_range)
            print("\nPerformance Analysis:")
            print("-" * 80)
            
            print("\nFunction Statistics:")
            for func, stats in results.get('function_stats', {}).items():
                print(f"\nFunction: {func}")
                print(f"Calls: {stats['calls']}")
                print(f"Average Time: {stats['avg_time']:.4f}s")
                print(f"Average Memory: {stats['avg_memory'] / 1024:.2f}KB")
                print(f"Success Rate: {stats['success_rate']:.1f}%")
            
            print("\nAPI Statistics:")
            for endpoint, stats in results.get('api_stats', {}).items():
                print(f"\nEndpoint: {endpoint}")
                print(f"Calls: {stats['calls']}")
                print(f"Average Time: {stats['avg_time']:.4f}s")
                print(f"Success Rate: {stats['success_rate']:.1f}%")
            
        elif args.action == 'system':
            metrics = profiler.get_system_metrics()
            print("\nSystem Metrics:")
            print("-" * 80)
            print(f"CPU Usage: {metrics['cpu']['overall']:.1f}%")
            print(f"Memory Usage: {metrics['memory']['percent']:.1f}%")
            print(f"Disk Usage: {metrics['disk']['percent']:.1f}%")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
