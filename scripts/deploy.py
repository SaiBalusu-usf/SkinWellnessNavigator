#!/usr/bin/env python3
"""
Deployment script for Skin Wellness Navigator.
Handles application deployment, environment configuration, and service management.
"""

import os
import sys
import subprocess
import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deploy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Deployer:
    """Handles application deployment and configuration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.env_file = self.project_root / '.env'
        self.backup_dir = self.project_root / 'backups'
        self.required_dirs = [
            'data',
            'logs',
            'uploads',
            'model_cache',
            'backups'
        ]

    def create_backup(self):
        """Create a backup of the current application state."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration files
            if self.env_file.exists():
                shutil.copy2(self.env_file, backup_path / '.env')
            
            # Backup data directory
            data_dir = self.project_root / 'data'
            if data_dir.exists():
                shutil.copytree(data_dir, backup_path / 'data')
            
            # Backup database
            db_file = self.project_root / 'data' / 'skin_wellness.db'
            if db_file.exists():
                shutil.copy2(db_file, backup_path)
            
            logger.info(f"Backup created at: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    def restore_backup(self, backup_path: Path):
        """
        Restore from a backup.
        
        Args:
            backup_path: Path to backup directory
        """
        try:
            # Restore configuration files
            env_backup = backup_path / '.env'
            if env_backup.exists():
                shutil.copy2(env_backup, self.env_file)
            
            # Restore data directory
            data_backup = backup_path / 'data'
            if data_backup.exists():
                data_dir = self.project_root / 'data'
                if data_dir.exists():
                    shutil.rmtree(data_dir)
                shutil.copytree(data_backup, data_dir)
            
            # Restore database
            db_backup = backup_path / 'skin_wellness.db'
            if db_backup.exists():
                db_file = self.project_root / 'data' / 'skin_wellness.db'
                shutil.copy2(db_backup, db_file)
            
            logger.info(f"Restored from backup: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            raise

    def setup_environment(self, env_type: str):
        """
        Set up environment configuration.
        
        Args:
            env_type: Environment type ('development', 'staging', 'production')
        """
        env_template = {
            'development': {
                'FLASK_ENV': 'development',
                'FLASK_DEBUG': 'True',
                'DATABASE_URL': 'sqlite:///data/skin_wellness.db',
                'SECRET_KEY': 'dev-secret-key',
                'GEMINI_API_KEY': '',
                'LOG_LEVEL': 'DEBUG'
            },
            'staging': {
                'FLASK_ENV': 'staging',
                'FLASK_DEBUG': 'False',
                'DATABASE_URL': 'sqlite:///data/skin_wellness.db',
                'SECRET_KEY': 'staging-secret-key',
                'GEMINI_API_KEY': '',
                'LOG_LEVEL': 'INFO'
            },
            'production': {
                'FLASK_ENV': 'production',
                'FLASK_DEBUG': 'False',
                'DATABASE_URL': 'sqlite:///data/skin_wellness.db',
                'SECRET_KEY': 'prod-secret-key',
                'GEMINI_API_KEY': '',
                'LOG_LEVEL': 'WARNING'
            }
        }
        
        try:
            # Create .env file
            env_config = env_template[env_type]
            
            with open(self.env_file, 'w') as f:
                for key, value in env_config.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Environment configured for: {env_type}")
            
        except Exception as e:
            logger.error(f"Error setting up environment: {e}")
            raise

    def check_dependencies(self) -> bool:
        """
        Check if all required dependencies are installed.
        
        Returns:
            bool: True if all dependencies are met
        """
        try:
            # Check Python packages
            result = subprocess.run(
                ["pip", "freeze"],
                capture_output=True,
                text=True,
                check=True
            )
            installed_packages = result.stdout.split('\n')
            
            with open('requirements.txt', 'r') as f:
                required_packages = f.read().split('\n')
            
            missing_packages = []
            for package in required_packages:
                if package and package not in installed_packages:
                    missing_packages.append(package)
            
            if missing_packages:
                logger.warning(f"Missing packages: {missing_packages}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False

    def setup_service(self):
        """Set up application as a system service."""
        service_template = """[Unit]
Description=Skin Wellness Navigator
After=network.target

[Service]
User={user}
WorkingDirectory={work_dir}
Environment="PATH={venv_path}/bin"
ExecStart={venv_path}/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # Get current user
            user = os.getenv('USER', 'nobody')
            venv_path = self.project_root / 'venv'
            
            # Create service file
            service_content = service_template.format(
                user=user,
                work_dir=self.project_root,
                venv_path=venv_path
            )
            
            service_path = Path('/etc/systemd/system/skin_wellness.service')
            
            # Write service file (requires sudo)
            subprocess.run(
                ['sudo', 'tee', service_path],
                input=service_content.encode(),
                check=True
            )
            
            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            
            logger.info("System service configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up service: {e}")
            raise

    def deploy(self, env_type: str):
        """
        Deploy the application.
        
        Args:
            env_type: Environment type to deploy
        """
        try:
            # Create backup
            logger.info("Creating backup...")
            self.create_backup()
            
            # Check dependencies
            logger.info("Checking dependencies...")
            if not self.check_dependencies():
                raise Exception("Missing dependencies")
            
            # Setup environment
            logger.info("Setting up environment...")
            self.setup_environment(env_type)
            
            # Initialize database
            logger.info("Initializing database...")
            subprocess.run(
                ['python', 'scripts/manage_db.py', 'init'],
                check=True
            )
            
            # Apply database migrations
            logger.info("Applying database migrations...")
            subprocess.run(
                ['python', 'scripts/manage_db.py', 'migrate'],
                check=True
            )
            
            # Setup service if production
            if env_type == 'production':
                logger.info("Setting up system service...")
                self.setup_service()
            
            logger.info(f"Deployment completed for {env_type} environment")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Application deployment tool")
    
    parser.add_argument(
        'action',
        choices=['deploy', 'backup', 'restore'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--env',
        choices=['development', 'staging', 'production'],
        default='development',
        help='Environment type'
    )
    
    parser.add_argument(
        '--backup-path',
        help='Path to backup directory for restore action'
    )
    
    args = parser.parse_args()
    
    deployer = Deployer()
    
    try:
        if args.action == 'deploy':
            deployer.deploy(args.env)
        elif args.action == 'backup':
            deployer.create_backup()
        elif args.action == 'restore':
            if not args.backup_path:
                parser.error("--backup-path required for restore action")
            deployer.restore_backup(Path(args.backup_path))
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
