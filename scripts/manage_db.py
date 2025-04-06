#!/usr/bin/env python3
"""
Database management script for Skin Wellness Navigator.
Handles database creation, migrations, and maintenance tasks.
"""

import os
import sys
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    """Manages database operations."""
    
    def __init__(self):
        self.db_path = Path('data/skin_wellness.db')
        self.migrations_path = Path('migrations')
        self.schema_version_table = 'schema_version'

    def init_db(self):
        """Initialize the database and create version tracking table."""
        print("Initializing database...")
        
        try:
            # Create data directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create schema version table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.schema_version_table} (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            # Create initial tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    image_path TEXT,
                    prediction TEXT,
                    confidence REAL,
                    clinical_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clinical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    diagnosis TEXT,
                    stage TEXT,
                    morphology TEXT,
                    treatment TEXT,
                    outcome TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("Database initialized successfully.")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            sys.exit(1)
        finally:
            conn.close()

    def create_migration(self, description):
        """Create a new migration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{description.lower().replace(' ', '_')}.sql"
        
        # Create migrations directory if it doesn't exist
        self.migrations_path.mkdir(parents=True, exist_ok=True)
        
        migration_file = self.migrations_path / filename
        migration_template = f"""-- Migration: {description}
-- Created at: {datetime.now().isoformat()}

-- Write your SQL statements here

-- Up
BEGIN TRANSACTION;

-- Add your schema changes here

COMMIT;

-- Down
BEGIN TRANSACTION;

-- Add your rollback statements here

COMMIT;
"""
        
        migration_file.write_text(migration_template)
        print(f"Created migration file: {filename}")

    def apply_migrations(self):
        """Apply pending migrations."""
        print("Applying migrations...")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get applied migrations
            cursor.execute(f"SELECT version FROM {self.schema_version_table}")
            applied_versions = {row[0] for row in cursor.fetchall()}
            
            # Get all migration files
            migrations = sorted(self.migrations_path.glob("*.sql"))
            
            for migration in migrations:
                version = int(migration.name.split('_')[0])
                
                if version not in applied_versions:
                    print(f"Applying migration: {migration.name}")
                    
                    # Read migration file
                    sql = migration.read_text()
                    up_sql = sql.split('-- Down')[0].split('BEGIN TRANSACTION;')[1].strip()
                    
                    try:
                        # Apply migration
                        cursor.executescript(up_sql)
                        
                        # Record migration
                        cursor.execute(
                            f"INSERT INTO {self.schema_version_table} (version, description) VALUES (?, ?)",
                            (version, migration.name)
                        )
                        
                        conn.commit()
                        print(f"Successfully applied migration: {migration.name}")
                        
                    except Exception as e:
                        conn.rollback()
                        print(f"Error applying migration {migration.name}: {e}")
                        sys.exit(1)
            
            print("All migrations applied successfully.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            sys.exit(1)
        finally:
            conn.close()

    def rollback_migration(self, version=None):
        """
        Rollback the last migration or a specific version.
        
        Args:
            version: Specific version to rollback to
        """
        print("Rolling back migration...")
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get the last applied migration if version not specified
            if version is None:
                cursor.execute(
                    f"SELECT version FROM {self.schema_version_table} ORDER BY version DESC LIMIT 1"
                )
                result = cursor.fetchone()
                if not result:
                    print("No migrations to roll back.")
                    return
                version = result[0]
            
            # Find the migration file
            migration_file = next(self.migrations_path.glob(f"{version:08d}_*.sql"), None)
            if not migration_file:
                print(f"Migration file for version {version} not found.")
                return
            
            print(f"Rolling back migration: {migration_file.name}")
            
            # Read migration file
            sql = migration_file.read_text()
            down_sql = sql.split('-- Down')[1].split('BEGIN TRANSACTION;')[1].strip()
            
            try:
                # Apply rollback
                cursor.executescript(down_sql)
                
                # Remove migration record
                cursor.execute(
                    f"DELETE FROM {self.schema_version_table} WHERE version = ?",
                    (version,)
                )
                
                conn.commit()
                print(f"Successfully rolled back migration: {migration_file.name}")
                
            except Exception as e:
                conn.rollback()
                print(f"Error rolling back migration: {e}")
                sys.exit(1)
            
        except Exception as e:
            print(f"Error during rollback: {e}")
            sys.exit(1)
        finally:
            conn.close()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database management tool")
    
    parser.add_argument(
        'command',
        choices=['init', 'create', 'migrate', 'rollback'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--description',
        help='Migration description (required for create command)'
    )
    
    parser.add_argument(
        '--version',
        type=int,
        help='Version to rollback to'
    )
    
    args = parser.parse_args()
    
    db_manager = DatabaseManager()
    
    if args.command == 'init':
        db_manager.init_db()
    elif args.command == 'create':
        if not args.description:
            print("Error: --description is required for create command")
            sys.exit(1)
        db_manager.create_migration(args.description)
    elif args.command == 'migrate':
        db_manager.apply_migrations()
    elif args.command == 'rollback':
        db_manager.rollback_migration(args.version)

if __name__ == '__main__':
    main()
