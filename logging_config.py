import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """Configure logging for the application."""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Generate log filename with timestamp
    log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Configure logging format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_filename,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)

    # Console handler for INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Error log file handler
    error_log_filename = f"logs/error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_filename,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    error_file_handler.setFormatter(log_format)
    error_file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_file_handler)

    # Create specific loggers
    loggers = {
        'api': create_module_logger('api'),
        'model': create_module_logger('model'),
        'data': create_module_logger('data'),
        'security': create_module_logger('security')
    }

    return loggers

def create_module_logger(module_name):
    """Create a logger for a specific module."""
    logger = logging.getLogger(module_name)
    
    # Module-specific log file
    module_log_filename = f"logs/{module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    handler = logging.handlers.RotatingFileHandler(
        module_log_filename,
        maxBytes=5242880,  # 5MB
        backupCount=3
    )
    
    formatter = logging.Formatter(
        f'%(asctime)s - {module_name} - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def log_request_info(logger, request):
    """Log incoming request information."""
    logger.info(f"Request Method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request Headers: {dict(request.headers)}")
    logger.info(f"Request Remote Address: {request.remote_addr}")

def log_response_info(logger, response):
    """Log outgoing response information."""
    logger.info(f"Response Status: {response.status_code}")
    logger.info(f"Response Headers: {dict(response.headers)}")

def log_error(logger, error, additional_info=None):
    """Log error information with stack trace."""
    logger.error(f"Error: {str(error)}")
    if additional_info:
        logger.error(f"Additional Information: {additional_info}")
    logger.exception("Stack Trace:")

# Performance logging
def log_performance_metrics(logger, start_time, end_time, operation_name):
    """Log performance metrics for operations."""
    duration = end_time - start_time
    logger.info(f"Operation '{operation_name}' completed in {duration:.2f} seconds")

# Security logging
def log_security_event(logger, event_type, details):
    """Log security-related events."""
    logger.warning(f"Security Event - Type: {event_type}, Details: {details}")

# Model logging
def log_model_prediction(logger, input_shape, prediction, confidence):
    """Log model prediction information."""
    logger.info(f"Model Input Shape: {input_shape}")
    logger.info(f"Prediction: {prediction}")
    logger.info(f"Confidence: {confidence:.2f}")

# Data processing logging
def log_data_processing(logger, operation, input_size, output_size):
    """Log data processing operations."""
    logger.info(f"Data Processing - Operation: {operation}")
    logger.info(f"Input Size: {input_size}")
    logger.info(f"Output Size: {output_size}")

# System health logging
def log_system_health(logger, memory_usage, cpu_usage):
    """Log system health metrics."""
    logger.info(f"System Health - Memory Usage: {memory_usage}%")
    logger.info(f"System Health - CPU Usage: {cpu_usage}%")
