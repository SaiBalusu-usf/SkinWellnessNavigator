#!/usr/bin/env python3
"""
Monitoring script for Skin Wellness Navigator.
Collects system metrics, application performance data, and model statistics.
"""

import os
import sys
import time
import json
import psutil
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
from queue import Queue
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and stores system and application metrics."""
    
    def __init__(self, db_path: str = 'data/metrics.db'):
        self.db_path = db_path
        self.metrics_queue = Queue()
        self.running = False
        self._init_db()

    def _init_db(self):
        """Initialize the metrics database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_io_sent REAL,
                    network_io_received REAL
                )
            """)
            
            # Create application metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_metrics (
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT,
                    response_time REAL,
                    status_code INTEGER,
                    error_count INTEGER
                )
            """)
            
            # Create model metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_metrics (
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    inference_time REAL,
                    confidence_score REAL,
                    memory_usage REAL
                )
            """)
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error initializing metrics database: {e}")
            raise
        finally:
            conn.close()

    def collect_system_metrics(self) -> Dict:
        """Collect system metrics."""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_usage,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'network_io_sent': network.bytes_sent,
                'network_io_received': network.bytes_recv
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    def store_metrics(self, metrics: Dict, metric_type: str):
        """Store metrics in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if metric_type == 'system':
                cursor.execute("""
                    INSERT INTO system_metrics 
                    (cpu_usage, memory_usage, disk_usage, network_io_sent, network_io_received)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metrics['cpu_usage'],
                    metrics['memory_usage'],
                    metrics['disk_usage'],
                    metrics['network_io_sent'],
                    metrics['network_io_received']
                ))
            
            elif metric_type == 'app':
                cursor.execute("""
                    INSERT INTO app_metrics 
                    (endpoint, response_time, status_code, error_count)
                    VALUES (?, ?, ?, ?)
                """, (
                    metrics['endpoint'],
                    metrics['response_time'],
                    metrics['status_code'],
                    metrics['error_count']
                ))
            
            elif metric_type == 'model':
                cursor.execute("""
                    INSERT INTO model_metrics 
                    (model_name, inference_time, confidence_score, memory_usage)
                    VALUES (?, ?, ?, ?)
                """, (
                    metrics['model_name'],
                    metrics['inference_time'],
                    metrics['confidence_score'],
                    metrics['memory_usage']
                ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
        finally:
            conn.close()

    def get_metrics(self, metric_type: str, time_range: Optional[timedelta] = None) -> List[Dict]:
        """
        Retrieve metrics from the database.
        
        Args:
            metric_type: Type of metrics to retrieve ('system', 'app', or 'model')
            time_range: Optional time range to filter metrics
            
        Returns:
            List[Dict]: List of metric records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            table_name = f"{metric_type}_metrics"
            query = f"SELECT * FROM {table_name}"
            
            if time_range:
                cutoff = datetime.now() - time_range
                query += f" WHERE timestamp >= '{cutoff.isoformat()}'"
            
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            return []
        finally:
            conn.close()

    def start_collection(self, interval: int = 60):
        """
        Start collecting metrics in a background thread.
        
        Args:
            interval: Collection interval in seconds
        """
        def collector():
            while self.running:
                try:
                    metrics = self.collect_system_metrics()
                    self.metrics_queue.put(('system', metrics))
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in collector thread: {e}")
        
        def processor():
            while self.running:
                try:
                    metric_type, metrics = self.metrics_queue.get()
                    self.store_metrics(metrics, metric_type)
                    self.metrics_queue.task_done()
                except Exception as e:
                    logger.error(f"Error in processor thread: {e}")
        
        self.running = True
        
        # Start collector thread
        collector_thread = threading.Thread(target=collector)
        collector_thread.daemon = True
        collector_thread.start()
        
        # Start processor thread
        processor_thread = threading.Thread(target=processor)
        processor_thread.daemon = True
        processor_thread.start()

    def stop_collection(self):
        """Stop collecting metrics."""
        self.running = False

class MetricsAnalyzer:
    """Analyzes collected metrics and generates reports."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def generate_system_report(self, time_range: timedelta) -> Dict:
        """Generate system metrics report."""
        metrics = self.collector.get_metrics('system', time_range)
        
        if not metrics:
            return {}
        
        cpu_usage = [m['cpu_usage'] for m in metrics]
        memory_usage = [m['memory_usage'] for m in metrics]
        disk_usage = [m['disk_usage'] for m in metrics]
        
        return {
            'time_range': str(time_range),
            'cpu_usage': {
                'avg': sum(cpu_usage) / len(cpu_usage),
                'max': max(cpu_usage),
                'min': min(cpu_usage)
            },
            'memory_usage': {
                'avg': sum(memory_usage) / len(memory_usage),
                'max': max(memory_usage),
                'min': min(memory_usage)
            },
            'disk_usage': {
                'avg': sum(disk_usage) / len(disk_usage),
                'max': max(disk_usage),
                'min': min(disk_usage)
            }
        }

    def generate_model_report(self, time_range: timedelta) -> Dict:
        """Generate model performance report."""
        metrics = self.collector.get_metrics('model', time_range)
        
        if not metrics:
            return {}
        
        model_stats = {}
        for metric in metrics:
            model_name = metric['model_name']
            if model_name not in model_stats:
                model_stats[model_name] = {
                    'inference_times': [],
                    'confidence_scores': [],
                    'memory_usage': []
                }
            
            model_stats[model_name]['inference_times'].append(metric['inference_time'])
            model_stats[model_name]['confidence_scores'].append(metric['confidence_score'])
            model_stats[model_name]['memory_usage'].append(metric['memory_usage'])
        
        report = {'time_range': str(time_range)}
        for model_name, stats in model_stats.items():
            report[model_name] = {
                'avg_inference_time': sum(stats['inference_times']) / len(stats['inference_times']),
                'avg_confidence': sum(stats['confidence_scores']) / len(stats['confidence_scores']),
                'avg_memory_usage': sum(stats['memory_usage']) / len(stats['memory_usage'])
            }
        
        return report

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Metrics collection and monitoring")
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Collection interval in seconds'
    )
    
    parser.add_argument(
        '--report-type',
        choices=['system', 'model'],
        help='Generate a specific type of report'
    )
    
    parser.add_argument(
        '--time-range',
        type=int,
        default=24,
        help='Time range in hours for report generation'
    )
    
    args = parser.parse_args()
    
    collector = MetricsCollector()
    analyzer = MetricsAnalyzer(collector)
    
    def signal_handler(signum, frame):
        print("\nStopping metrics collection...")
        collector.stop_collection()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.report_type:
        time_range = timedelta(hours=args.time_range)
        if args.report_type == 'system':
            report = analyzer.generate_system_report(time_range)
        else:
            report = analyzer.generate_model_report(time_range)
        
        print(json.dumps(report, indent=2))
    else:
        print(f"Starting metrics collection (interval: {args.interval}s)")
        collector.start_collection(args.interval)
        
        while True:
            time.sleep(1)

if __name__ == '__main__':
    main()
