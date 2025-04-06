import os
from datetime import timedelta
from typing import Dict, Any

class BaseConfig:
    """Base configuration class."""
    
    # Application Settings
    APP_NAME = "Skin Wellness Navigator"
    VERSION = "1.0.0"
    
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # API Settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Image Processing Settings
    IMAGE_SIZE = (299, 299)
    BATCH_SIZE = 32
    
    # Model Settings
    MODEL_CONFIDENCE_THRESHOLD = 0.8
    MODEL_CACHE_DIR = 'model_cache'
    
    # Clinical Data Settings
    CLINICAL_DATA_PATH = os.getenv('CLINICAL_DATA_PATH', 'clinical.csv')
    DATA_CACHE_TIMEOUT = 3600  # 1 hour
    
    # Logging Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    LOG_DIR = 'logs'
    
    # Security Settings
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Cache Settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Monitoring Settings
    ENABLE_MONITORING = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', 9090))
    
    # Error Tracking
    SENTRY_DSN = os.getenv('SENTRY_DSN', '')
    
    # Health Check Settings
    HEALTH_CHECK_ENDPOINTS = {
        'api': '/api/health',
        'db': '/health/db',
        'cache': '/health/cache'
    }
    
    # System Monitoring Thresholds
    SYSTEM_MONITORING = {
        'cpu_threshold': 90,  # percentage
        'memory_threshold': 90,  # percentage
        'disk_threshold': 90,  # percentage
        'check_interval': 300  # seconds
    }

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    SQLALCHEMY_ECHO = True
    EXPLAIN_TEMPLATE_LOADING = True
    TEMPLATES_AUTO_RELOAD = True
    
    # Development database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
        'sqlite:///dev.db'
    )
    
    # Mail settings for development
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'development@example.com'

class TestingConfig(BaseConfig):
    """Testing configuration."""
    
    DEBUG = True
    TESTING = True
    
    # Test database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'sqlite:///test.db'
    )
    
    # Disable CSRF tokens in testing
    WTF_CSRF_ENABLED = False
    
    # Test-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    LIVESERVER_PORT = 8943
    LIVESERVER_TIMEOUT = 10

class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Production database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Production mail settings
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Production-specific monitoring
    ENABLE_MONITORING = True
    
    # Production-specific error tracking
    SENTRY_ENVIRONMENT = 'production'

class StagingConfig(ProductionConfig):
    """Staging configuration."""
    
    # Staging-specific settings
    STAGING = True
    
    # Staging database
    SQLALCHEMY_DATABASE_URI = os.getenv('STAGING_DATABASE_URL')
    
    # Staging-specific monitoring
    SENTRY_ENVIRONMENT = 'staging'

def get_config() -> Dict[str, Any]:
    """Get configuration based on environment."""
    
    env = os.getenv('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
        'staging': StagingConfig
    }
    
    return configs.get(env, DevelopmentConfig)

# Constants
HTTP_STATUS_CODES = {
    'OK': 200,
    'CREATED': 201,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

ERROR_MESSAGES = {
    'INVALID_FILE': 'Invalid file type. Please upload a valid image file.',
    'FILE_TOO_LARGE': 'File size too large. Maximum size is 16MB.',
    'PROCESSING_ERROR': 'Error processing the image.',
    'MODEL_ERROR': 'Error during model prediction.',
    'DATA_ERROR': 'Error accessing clinical data.',
    'API_ERROR': 'Error communicating with external API.',
    'AUTH_ERROR': 'Authentication error.',
    'RATE_LIMIT': 'Rate limit exceeded. Please try again later.'
}

# API Response Templates
API_RESPONSE_TEMPLATES = {
    'success': {
        'status': 'success',
        'code': HTTP_STATUS_CODES['OK'],
        'data': None,
        'message': None
    },
    'error': {
        'status': 'error',
        'code': HTTP_STATUS_CODES['INTERNAL_SERVER_ERROR'],
        'error': None,
        'message': None
    }
}
