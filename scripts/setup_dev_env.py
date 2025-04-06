#!/usr/bin/env python3
"""
Setup script for Skin Wellness Navigator development environment.
Creates necessary directories, installs dependencies, and initializes the project.
"""

import os
import sys
import subprocess
import venv
import platform
import shutil
from pathlib import Path

class DevEnvironmentSetup:
    """Handles development environment setup."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.venv_path = self.project_root / 'venv'
        self.required_dirs = [
            'data',
            'logs',
            'uploads',
            'model_cache',
            'coverage_reports',
            'test_results'
        ]
        
        # Determine OS-specific python executable
        self.python_executable = 'python.exe' if platform.system() == 'Windows' else 'python'
        self.pip_executable = 'pip.exe' if platform.system() == 'Windows' else 'pip'

    def create_virtual_environment(self):
        """Create a virtual environment."""
        print("\nCreating virtual environment...")
        try:
            venv.create(self.venv_path, with_pip=True)
            print("Virtual environment created successfully.")
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            sys.exit(1)

    def get_venv_python(self):
        """Get the path to the virtual environment's Python executable."""
        if platform.system() == 'Windows':
            return self.venv_path / 'Scripts' / self.python_executable
        return self.venv_path / 'bin' / self.python_executable

    def get_venv_pip(self):
        """Get the path to the virtual environment's pip executable."""
        if platform.system() == 'Windows':
            return self.venv_path / 'Scripts' / self.pip_executable
        return self.venv_path / 'bin' / self.pip_executable

    def install_dependencies(self):
        """Install project dependencies."""
        print("\nInstalling dependencies...")
        pip_path = self.get_venv_pip()
        
        try:
            # Upgrade pip
            subprocess.run(
                [str(pip_path), "install", "--upgrade", "pip"],
                check=True
            )
            
            # Install requirements
            subprocess.run(
                [str(pip_path), "install", "-r", "requirements.txt"],
                check=True
            )
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            sys.exit(1)

    def create_directories(self):
        """Create necessary project directories."""
        print("\nCreating project directories...")
        try:
            for directory in self.required_dirs:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {directory}")
        except Exception as e:
            print(f"Error creating directories: {e}")
            sys.exit(1)

    def generate_sample_data(self):
        """Generate sample clinical data."""
        print("\nGenerating sample data...")
        try:
            python_path = self.get_venv_python()
            subprocess.run(
                [str(python_path), "scripts/generate_sample_data.py"],
                check=True
            )
            print("Sample data generated successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error generating sample data: {e}")
            sys.exit(1)

    def setup_git_hooks(self):
        """Set up Git hooks for development."""
        print("\nSetting up Git hooks...")
        hooks_dir = self.project_root / '.git' / 'hooks'
        
        if not hooks_dir.exists():
            print("Git hooks directory not found. Skipping...")
            return
        
        # Pre-commit hook
        pre_commit = hooks_dir / 'pre-commit'
        pre_commit_content = """#!/bin/sh
# Run tests before commit
python run_tests.py
"""
        pre_commit.write_text(pre_commit_content)
        pre_commit.chmod(0o755)
        
        print("Git hooks set up successfully.")

    def verify_setup(self):
        """
        Verify the development environment setup.
        
        Returns:
            bool: True if all checks pass, False otherwise
        """
        print("\nVerifying setup...")
        
        # Define checks as a list of tuples (check_function, message)
        checks = [
            (lambda: self.venv_path.exists(), "Virtual environment exists"),
            (lambda: self.get_venv_python().exists(), "Python executable exists"),
            (lambda: self.get_venv_pip().exists(), "Pip executable exists")
        ]
        
        # Add directory checks
        for dir_name in self.required_dirs:
            dir_path = self.project_root / dir_name
            checks.append(
                (lambda p=dir_path: p.exists(), f"{dir_name} directory exists")
            )
        
        # Run all checks
        all_passed = True
        for check_func, message in checks:
            status = check_func()
            status_symbol = "✓" if status else "✗"
            print(f"{status_symbol} {message}")
            if not status:
                all_passed = False
        
        return all_passed

    def setup(self):
        """Run the complete setup process."""
        print("Starting development environment setup...")
        print(f"Project root: {self.project_root}")
        
        try:
            self.create_virtual_environment()
            self.create_directories()
            self.install_dependencies()
            self.generate_sample_data()
            self.setup_git_hooks()
            
            if self.verify_setup():
                print("\nSetup completed successfully!")
                print("\nTo activate the virtual environment:")
                if platform.system() == 'Windows':
                    print(f"    {self.venv_path}\\Scripts\\activate")
                else:
                    print(f"    source {self.venv_path}/bin/activate")
            else:
                print("\nSetup completed with some issues. Please check the verification results above.")
                
        except KeyboardInterrupt:
            print("\nSetup interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\nError during setup: {e}")
            sys.exit(1)

def main():
    """Main entry point."""
    setup = DevEnvironmentSetup()
    setup.setup()

if __name__ == '__main__':
    main()
