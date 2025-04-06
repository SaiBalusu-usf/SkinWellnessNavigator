#!/usr/bin/env python3
"""
Model management script for Skin Wellness Navigator.
Handles model downloading, caching, and version management.
"""

import os
import sys
import json
import hashlib
import requests
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelManager:
    """Manages AI model operations."""
    
    def __init__(self):
        self.model_dir = Path('model_cache')
        self.model_info_file = self.model_dir / 'model_info.json'
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.current_models = self._load_model_info()

    def _load_model_info(self) -> Dict:
        """Load model information from JSON file."""
        if self.model_info_file.exists():
            try:
                return json.loads(self.model_info_file.read_text())
            except json.JSONDecodeError:
                logger.error("Error reading model info file")
                return {}
        return {}

    def _save_model_info(self):
        """Save model information to JSON file."""
        try:
            self.model_info_file.write_text(json.dumps(self.current_models, indent=2))
        except Exception as e:
            logger.error(f"Error saving model info: {e}")

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def download_model(self, model_url: str, model_name: str) -> bool:
        """
        Download a model from the specified URL.
        
        Args:
            model_url: URL to download the model from
            model_name: Name to save the model as
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Downloading model: {model_name}")
        
        try:
            # Download to temporary file first
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                response = requests.get(model_url, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024
                downloaded = 0
                
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    temp_file.write(data)
                    
                    if total_size:
                        percent = int((downloaded / total_size) * 100)
                        sys.stdout.write(f"\rDownload progress: {percent}%")
                        sys.stdout.flush()
            
            # Calculate hash
            model_hash = self._calculate_hash(Path(temp_file.name))
            
            # Move to final location
            model_path = self.model_dir / f"{model_name}.pt"
            os.replace(temp_file.name, model_path)
            
            # Update model info
            self.current_models[model_name] = {
                'path': str(model_path),
                'hash': model_hash,
                'downloaded_at': datetime.now().isoformat(),
                'url': model_url
            }
            
            self._save_model_info()
            logger.info(f"Model {model_name} downloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            if 'temp_file' in locals():
                os.unlink(temp_file.name)
            return False

    def verify_model(self, model_name: str) -> bool:
        """
        Verify model integrity using stored hash.
        
        Args:
            model_name: Name of the model to verify
            
        Returns:
            bool: True if verification passes, False otherwise
        """
        if model_name not in self.current_models:
            logger.error(f"Model {model_name} not found")
            return False
            
        model_info = self.current_models[model_name]
        model_path = Path(model_info['path'])
        
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False
            
        current_hash = self._calculate_hash(model_path)
        stored_hash = model_info['hash']
        
        if current_hash != stored_hash:
            logger.error(f"Hash mismatch for model {model_name}")
            return False
            
        logger.info(f"Model {model_name} verified successfully")
        return True

    def list_models(self) -> List[Dict]:
        """
        List all downloaded models and their information.
        
        Returns:
            List[Dict]: List of model information
        """
        models = []
        for name, info in self.current_models.items():
            model_path = Path(info['path'])
            models.append({
                'name': name,
                'size': model_path.stat().st_size if model_path.exists() else 0,
                'downloaded_at': info['downloaded_at'],
                'verified': self.verify_model(name)
            })
        return models

    def remove_model(self, model_name: str) -> bool:
        """
        Remove a model and its information.
        
        Args:
            model_name: Name of the model to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if model_name not in self.current_models:
            logger.error(f"Model {model_name} not found")
            return False
            
        try:
            model_path = Path(self.current_models[model_name]['path'])
            if model_path.exists():
                model_path.unlink()
            
            del self.current_models[model_name]
            self._save_model_info()
            
            logger.info(f"Model {model_name} removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error removing model: {e}")
            return False

    def get_model_path(self, model_name: str) -> Optional[Path]:
        """
        Get the path to a model file.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Optional[Path]: Path to the model file if it exists
        """
        if model_name not in self.current_models:
            return None
            
        model_path = Path(self.current_models[model_name]['path'])
        return model_path if model_path.exists() else None

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Model management tool")
    
    parser.add_argument(
        'action',
        choices=['download', 'verify', 'list', 'remove'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--name',
        help='Model name'
    )
    
    parser.add_argument(
        '--url',
        help='URL to download model from'
    )
    
    args = parser.parse_args()
    
    manager = ModelManager()
    
    if args.action == 'download':
        if not args.name or not args.url:
            print("Error: --name and --url required for download")
            sys.exit(1)
        success = manager.download_model(args.url, args.name)
        sys.exit(0 if success else 1)
        
    elif args.action == 'verify':
        if not args.name:
            print("Error: --name required for verify")
            sys.exit(1)
        success = manager.verify_model(args.name)
        sys.exit(0 if success else 1)
        
    elif args.action == 'list':
        models = manager.list_models()
        print("\nDownloaded Models:")
        print("-" * 80)
        for model in models:
            print(f"Name: {model['name']}")
            print(f"Size: {model['size'] / 1024 / 1024:.2f} MB")
            print(f"Downloaded: {model['downloaded_at']}")
            print(f"Verified: {'Yes' if model['verified'] else 'No'}")
            print("-" * 80)
            
    elif args.action == 'remove':
        if not args.name:
            print("Error: --name required for remove")
            sys.exit(1)
        success = manager.remove_model(args.name)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
