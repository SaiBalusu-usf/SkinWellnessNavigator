#!/usr/bin/env python3
"""
Error tracking and reporting script for Skin Wellness Navigator.
Handles error logging, aggregation, and notification.
"""

import os
import sys
import json
import logging
import sqlite3
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from queue import Queue
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/error_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ErrorTracker:
    """Handles error tracking and reporting."""
    
    def __init__(self, db_path: str = 'data/errors.db'):
        self.db_path = db_path
        self.error_queue = Queue()
        self.running = False
        self.notification_threshold = 5  # Number of similar errors before notification
        self.notification_interval = timedelta(hours=1)
        self._init_db()

    def _init_db(self):
        """Initialize error tracking database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create errors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    traceback TEXT,
                    module TEXT,
                    line_number INTEGER,
                    user_id INTEGER,
                    request_data TEXT,
                    environment TEXT,
                    resolved BOOLEAN DEFAULT 0
                )
            """)
            
            # Create error notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_notified DATETIME,
                    notification_count INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            conn.close()

    def track_error(self, error: Exception, **context):
        """
        Track an error with context.
        
        Args:
            error: Exception object
            **context: Additional context (user_id, request_data, etc.)
        """
        error_info = {
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'traceback': ''.join(traceback.format_tb(error.__traceback__)),
            'module': getattr(error, '__module__', 'unknown'),
            'line_number': self._get_error_line(error),
            'environment': os.getenv('FLASK_ENV', 'development'),
            **context
        }
        
        self.error_queue.put(error_info)

    def _get_error_line(self, error: Exception) -> Optional[int]:
        """Extract line number from error traceback."""
        tb = error.__traceback__
        while tb.tb_next:
            tb = tb.tb_next
        return tb.tb_lineno

    def _store_error(self, error_info: Dict):
        """Store error information in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store error
            cursor.execute("""
                INSERT INTO errors (
                    error_type, error_message, traceback, module,
                    line_number, user_id, request_data, environment
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                error_info['error_type'],
                error_info['error_message'],
                error_info['traceback'],
                error_info['module'],
                error_info['line_number'],
                error_info.get('user_id'),
                json.dumps(error_info.get('request_data', {})),
                error_info['environment']
            ))
            
            # Update error notifications
            cursor.execute("""
                INSERT INTO error_notifications (error_type)
                VALUES (?)
                ON CONFLICT(error_type) DO UPDATE SET
                    count = count + 1,
                    last_seen = CURRENT_TIMESTAMP
            """, (error_info['error_type'],))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing error information: {e}")
        finally:
            conn.close()

    def _should_notify(self, error_type: str) -> bool:
        """Check if notification should be sent for error type."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT count, last_notified
                FROM error_notifications
                WHERE error_type = ?
            """, (error_type,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            count, last_notified = result
            
            if count >= self.notification_threshold:
                if not last_notified or datetime.now() - datetime.fromisoformat(last_notified) > self.notification_interval:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking notification status: {e}")
            return False
        finally:
            conn.close()

    def send_notification(self, error_type: str):
        """Send error notification."""
        try:
            # Get error details
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as error_count,
                       MIN(timestamp) as first_seen,
                       MAX(timestamp) as last_seen
                FROM errors
                WHERE error_type = ?
                AND timestamp > datetime('now', '-1 day')
            """, (error_type,))
            
            result = cursor.fetchone()
            if not result:
                return
            
            error_count, first_seen, last_seen = result
            
            # Prepare email
            msg = MIMEMultipart()
            msg['Subject'] = f'Error Alert: {error_type}'
            msg['From'] = os.getenv('MAIL_DEFAULT_SENDER', 'alerts@skinwellnessnavigator.com')
            msg['To'] = os.getenv('ERROR_NOTIFICATION_EMAIL', 'admin@skinwellnessnavigator.com')
            
            body = f"""
Error Type: {error_type}
Error Count: {error_count}
First Seen: {first_seen}
Last Seen: {last_seen}

Please check the error tracking system for more details.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(os.getenv('MAIL_SERVER', 'localhost')) as server:
                if os.getenv('MAIL_USE_TLS', 'true').lower() == 'true':
                    server.starttls()
                if os.getenv('MAIL_USERNAME'):
                    server.login(
                        os.getenv('MAIL_USERNAME'),
                        os.getenv('MAIL_PASSWORD')
                    )
                server.send_message(msg)
            
            # Update notification timestamp
            cursor.execute("""
                UPDATE error_notifications
                SET last_notified = CURRENT_TIMESTAMP,
                    notification_count = notification_count + 1
                WHERE error_type = ?
            """, (error_type,))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def start_tracking(self):
        """Start error tracking in background thread."""
        def processor():
            while self.running:
                try:
                    error_info = self.error_queue.get()
                    self._store_error(error_info)
                    
                    if self._should_notify(error_info['error_type']):
                        self.send_notification(error_info['error_type'])
                    
                    self.error_queue.task_done()
                except Exception as e:
                    logger.error(f"Error in processor thread: {e}")
        
        self.running = True
        
        processor_thread = threading.Thread(target=processor)
        processor_thread.daemon = True
        processor_thread.start()

    def stop_tracking(self):
        """Stop error tracking."""
        self.running = False

    def get_error_summary(self, time_range: timedelta = timedelta(days=1)) -> Dict:
        """
        Get error summary for time range.
        
        Args:
            time_range: Time range to summarize
            
        Returns:
            Dict: Error summary statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff = datetime.now() - time_range
            
            cursor.execute("""
                SELECT error_type,
                       COUNT(*) as error_count,
                       MIN(timestamp) as first_seen,
                       MAX(timestamp) as last_seen
                FROM errors
                WHERE timestamp > ?
                GROUP BY error_type
                ORDER BY error_count DESC
            """, (cutoff.isoformat(),))
            
            summary = {
                'time_range': str(time_range),
                'total_errors': 0,
                'error_types': []
            }
            
            for row in cursor.fetchall():
                error_type, count, first_seen, last_seen = row
                summary['total_errors'] += count
                summary['error_types'].append({
                    'type': error_type,
                    'count': count,
                    'first_seen': first_seen,
                    'last_seen': last_seen
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
        finally:
            conn.close()

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Error tracking tool")
    
    parser.add_argument(
        'action',
        choices=['start', 'summary'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days for summary'
    )
    
    args = parser.parse_args()
    
    tracker = ErrorTracker()
    
    if args.action == 'start':
        def signal_handler(signum, frame):
            print("\nStopping error tracker...")
            tracker.stop_tracking()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        print("Starting error tracker...")
        tracker.start_tracking()
        
        while True:
            try:
                signal.pause()
            except AttributeError:
                # Windows doesn't support signal.pause()
                import time
                time.sleep(1)
                
    elif args.action == 'summary':
        summary = tracker.get_error_summary(timedelta(days=args.days))
        print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
