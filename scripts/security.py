#!/usr/bin/env python3
"""
Security management script for Skin Wellness Navigator.
Handles user authentication, authorization, and security configurations.
"""

import os
import sys
import json
import hashlib
import secrets
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security operations and user authentication."""
    
    def __init__(self, db_path: str = 'data/skin_wellness.db'):
        self.db_path = db_path
        self.ph = PasswordHasher()
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
        self._init_db()

    def _init_db(self):
        """Initialize security-related database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create access tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_revoked BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create security audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    ip_address TEXT,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error initializing security database: {e}")
            raise
        finally:
            conn.close()

    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> bool:
        """
        Create a new user.
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            role: User role
            
        Returns:
            bool: True if successful
        """
        try:
            # Hash password
            password_hash = self.ph.hash(password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (username, email, password_hash, role))
            
            conn.commit()
            logger.info(f"Created user: {username}")
            return True
            
        except sqlite3.IntegrityError:
            logger.error(f"User already exists: {username}")
            return False
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
        finally:
            conn.close()

    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Verify user credentials.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Optional[Dict]: User information if verified
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, password_hash, role
                FROM users
                WHERE username = ? AND is_active = 1
            """, (username,))
            
            user = cursor.fetchone()
            if not user:
                return None
            
            try:
                self.ph.verify(user[3], password)
                
                # Update last login
                cursor.execute("""
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (user[0],))
                
                conn.commit()
                
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[4]
                }
                
            except VerifyMismatchError:
                return None
                
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return None
        finally:
            conn.close()

    def generate_token(self, user_id: int, expiry: timedelta = timedelta(hours=1)) -> Optional[str]:
        """
        Generate JWT token for user.
        
        Args:
            user_id: User ID
            expiry: Token expiry time
            
        Returns:
            Optional[str]: JWT token
        """
        try:
            expires_at = datetime.utcnow() + expiry
            
            payload = {
                'user_id': user_id,
                'exp': expires_at
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            
            # Store token in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO access_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, token, expires_at))
            
            conn.commit()
            
            return token
            
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            Optional[Dict]: Token payload if valid
        """
        try:
            # Check if token is revoked
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT is_revoked
                FROM access_tokens
                WHERE token = ?
            """, (token,))
            
            result = cursor.fetchone()
            if not result or result[0]:
                return None
            
            # Verify token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def revoke_token(self, token: str) -> bool:
        """
        Revoke an access token.
        
        Args:
            token: JWT token
            
        Returns:
            bool: True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE access_tokens
                SET is_revoked = 1
                WHERE token = ?
            """, (token,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
        finally:
            conn.close()

    def log_security_event(self, event_type: str, user_id: Optional[int], ip_address: str, details: str):
        """Log security-related events."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO security_audit_log (event_type, user_id, ip_address, details)
                VALUES (?, ?, ?, ?)
            """, (event_type, user_id, ip_address, details))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
        finally:
            conn.close()

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security management tool")
    
    parser.add_argument(
        'action',
        choices=['create-user', 'verify-user', 'revoke-token'],
        help='Action to perform'
    )
    
    parser.add_argument('--username', help='Username')
    parser.add_argument('--email', help='Email address')
    parser.add_argument('--password', help='Password')
    parser.add_argument('--role', default='user', help='User role')
    parser.add_argument('--token', help='JWT token')
    
    args = parser.parse_args()
    
    security = SecurityManager()
    
    try:
        if args.action == 'create-user':
            if not all([args.username, args.email, args.password]):
                parser.error("Username, email, and password required")
            
            success = security.create_user(
                args.username,
                args.email,
                args.password,
                args.role
            )
            
            if success:
                print(f"User {args.username} created successfully")
            else:
                print("Failed to create user")
                sys.exit(1)
                
        elif args.action == 'verify-user':
            if not all([args.username, args.password]):
                parser.error("Username and password required")
            
            user = security.verify_user(args.username, args.password)
            if user:
                print("User verified successfully")
                print(json.dumps(user, indent=2))
            else:
                print("Invalid credentials")
                sys.exit(1)
                
        elif args.action == 'revoke-token':
            if not args.token:
                parser.error("Token required")
            
            success = security.revoke_token(args.token)
            if success:
                print("Token revoked successfully")
            else:
                print("Failed to revoke token")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
