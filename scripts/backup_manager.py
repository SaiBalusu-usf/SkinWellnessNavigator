#!/usr/bin/env python3
"""
Backup management script for Skin Wellness Navigator.
Handles data backup, restoration, and archival.
"""

import os
import sys
import json
import shutil
import logging
import sqlite3
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import schedule
import time
import threading
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupManager:
    """Manages data backup and restoration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.backup_dir = self.project_root / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.backup_queue = Queue()
        self.running = False
        
        # Directories to backup
        self.backup_paths = [
            'data',
            'uploads',
            'logs',
            'model_cache'
        ]
        
        # Files to backup
        self.backup_files = [
            '.env',
            'config.py',
            'requirements.txt'
        ]

    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """
        Create a backup of the application data.
        
        Args:
            backup_name: Optional name for the backup
            
        Returns:
            Path: Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_name or f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Create temporary directory for backup
            temp_dir = backup_path.with_suffix('.temp')
            temp_dir.mkdir(parents=True)
            
            # Copy directories
            for dir_name in self.backup_paths:
                src_path = self.project_root / dir_name
                if src_path.exists():
                    dst_path = temp_dir / dir_name
                    shutil.copytree(src_path, dst_path)
            
            # Copy files
            for file_name in self.backup_files:
                src_path = self.project_root / file_name
                if src_path.exists():
                    shutil.copy2(src_path, temp_dir)
            
            # Create backup manifest
            manifest = {
                'timestamp': timestamp,
                'name': backup_name,
                'contents': {
                    'directories': self.backup_paths,
                    'files': self.backup_files
                },
                'checksums': self._calculate_checksums(temp_dir)
            }
            
            manifest_path = temp_dir / 'manifest.json'
            manifest_path.write_text(json.dumps(manifest, indent=2))
            
            # Create tarball
            backup_file = backup_path.with_suffix('.tar.gz')
            with tarfile.open(backup_file, 'w:gz') as tar:
                tar.add(temp_dir, arcname=backup_name)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            logger.info(f"Backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if successful
        """
        try:
            # Create temporary directory for restoration
            temp_dir = self.backup_dir / 'restore_temp'
            temp_dir.mkdir(parents=True)
            
            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Find backup directory (should be only directory)
            backup_contents = list(temp_dir.iterdir())[0]
            
            # Verify manifest
            manifest_path = backup_contents / 'manifest.json'
            if not manifest_path.exists():
                raise ValueError("Invalid backup: manifest not found")
            
            manifest = json.loads(manifest_path.read_text())
            
            # Verify checksums
            current_checksums = self._calculate_checksums(backup_contents)
            if current_checksums != manifest['checksums']:
                raise ValueError("Backup integrity check failed")
            
            # Create backup of current state
            self.create_backup("pre_restore_backup")
            
            # Restore directories
            for dir_name in manifest['contents']['directories']:
                src_path = backup_contents / dir_name
                if src_path.exists():
                    dst_path = self.project_root / dir_name
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
            
            # Restore files
            for file_name in manifest['contents']['files']:
                src_path = backup_contents / file_name
                if src_path.exists():
                    dst_path = self.project_root / file_name
                    shutil.copy2(src_path, dst_path)
            
            logger.info(f"Backup restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
        finally:
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _calculate_checksums(self, directory: Path) -> Dict[str, str]:
        """Calculate SHA-256 checksums for all files in directory."""
        checksums = {}
        
        for path in directory.rglob('*'):
            if path.is_file():
                relative_path = str(path.relative_to(directory))
                sha256_hash = hashlib.sha256()
                
                with open(path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                
                checksums[relative_path] = sha256_hash.hexdigest()
        
        return checksums

    def list_backups(self) -> List[Dict]:
        """
        List available backups.
        
        Returns:
            List[Dict]: List of backup information
        """
        backups = []
        
        for backup_file in self.backup_dir.glob('*.tar.gz'):
            try:
                with tarfile.open(backup_file, 'r:gz') as tar:
                    manifest_info = None
                    for member in tar.getmembers():
                        if member.name.endswith('manifest.json'):
                            manifest_data = tar.extractfile(member)
                            manifest_info = json.loads(manifest_data.read())
                            break
                
                if manifest_info:
                    backups.append({
                        'file': backup_file.name,
                        'size': backup_file.stat().st_size,
                        'created': manifest_info['timestamp'],
                        'name': manifest_info['name']
                    })
                    
            except Exception as e:
                logger.error(f"Error reading backup {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)

    def cleanup_old_backups(self, max_age: timedelta = timedelta(days=30)):
        """Remove backups older than specified age."""
        try:
            cutoff = datetime.now() - max_age
            
            for backup in self.list_backups():
                backup_date = datetime.strptime(backup['created'], "%Y%m%d_%H%M%S")
                if backup_date < cutoff:
                    backup_path = self.backup_dir / backup['file']
                    backup_path.unlink()
                    logger.info(f"Removed old backup: {backup['file']}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")

    def start_scheduled_backups(self, interval_hours: int = 24):
        """Start scheduled backup creation."""
        def backup_job():
            try:
                self.create_backup()
                self.cleanup_old_backups()
            except Exception as e:
                logger.error(f"Error in scheduled backup: {e}")
        
        schedule.every(interval_hours).hours.do(backup_job)
        
        self.running = True
        while self.running:
            schedule.run_pending()
            time.sleep(60)

    def stop_scheduled_backups(self):
        """Stop scheduled backups."""
        self.running = False

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup management tool")
    
    parser.add_argument(
        'action',
        choices=['create', 'restore', 'list', 'schedule', 'cleanup'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--name',
        help='Backup name (for create action)'
    )
    
    parser.add_argument(
        '--file',
        help='Backup file to restore from'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=24,
        help='Backup interval in hours (for schedule action)'
    )
    
    parser.add_argument(
        '--max-age',
        type=int,
        default=30,
        help='Maximum backup age in days (for cleanup action)'
    )
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    try:
        if args.action == 'create':
            manager.create_backup(args.name)
            
        elif args.action == 'restore':
            if not args.file:
                parser.error("--file required for restore action")
            
            backup_path = Path(args.file)
            if not backup_path.is_absolute():
                backup_path = manager.backup_dir / args.file
            
            if manager.restore_backup(backup_path):
                print("Backup restored successfully")
            else:
                print("Failed to restore backup")
                sys.exit(1)
                
        elif args.action == 'list':
            backups = manager.list_backups()
            print("\nAvailable Backups:")
            print("-" * 80)
            for backup in backups:
                print(f"Name: {backup['name']}")
                print(f"File: {backup['file']}")
                print(f"Size: {backup['size'] / 1024 / 1024:.2f} MB")
                print(f"Created: {backup['created']}")
                print("-" * 80)
                
        elif args.action == 'schedule':
            print(f"Starting scheduled backups (interval: {args.interval} hours)")
            try:
                manager.start_scheduled_backups(args.interval)
            except KeyboardInterrupt:
                print("\nStopping scheduled backups...")
                manager.stop_scheduled_backups()
                
        elif args.action == 'cleanup':
            manager.cleanup_old_backups(timedelta(days=args.max_age))
            print("Old backups cleaned up")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
