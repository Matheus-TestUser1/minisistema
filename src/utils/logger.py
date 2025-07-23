"""
Logger Configuration Module
Sets up logging for the PDV system
"""
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str = 'pdv_system',
    log_level: str = 'INFO',
    log_dir: str = 'logs',
    console_output: bool = True,
    file_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        console_output: Enable console output
        file_output: Enable file output
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    
    # Ensure log directory exists
    if file_output and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Error file handler (always enabled if file_output is True)
    if file_output:
        error_log_file = os.path.join(log_dir, f'{name}_errors_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    logger.info(f"Logger '{name}' initialized with level {log_level}")
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger

class PDVLogger:
    """
    Custom logger class for PDV system with specific methods
    """
    
    def __init__(self, name: str = 'pdv_system', config: Optional[dict] = None):
        self.name = name
        self.config = config or {}
        
        # Setup logger with config
        self.logger = setup_logger(
            name=name,
            log_level=self.config.get('log_level', 'INFO'),
            log_dir=self.config.get('log_dir', 'logs'),
            console_output=self.config.get('console_output', True),
            file_output=self.config.get('file_output', True),
            max_file_size=self.config.get('max_file_size', 10 * 1024 * 1024),
            backup_count=self.config.get('backup_count', 5)
        )
    
    def log_user_action(self, action: str, user: str = 'system', details: str = ''):
        """Log user actions"""
        self.logger.info(f"USER_ACTION | User: {user} | Action: {action} | Details: {details}")
    
    def log_database_operation(self, operation: str, table: str = '', result: str = 'success', details: str = ''):
        """Log database operations"""
        self.logger.info(f"DB_OPERATION | Operation: {operation} | Table: {table} | Result: {result} | Details: {details}")
    
    def log_sync_operation(self, operation: str, status: str, details: str = ''):
        """Log synchronization operations"""
        self.logger.info(f"SYNC_OPERATION | Operation: {operation} | Status: {status} | Details: {details}")
    
    def log_business_event(self, event_type: str, event_data: dict):
        """Log business events (sales, receipts, etc.)"""
        details = " | ".join([f"{k}: {v}" for k, v in event_data.items()])
        self.logger.info(f"BUSINESS_EVENT | Type: {event_type} | {details}")
    
    def log_error(self, error: Exception, context: str = ''):
        """Log errors with context"""
        self.logger.error(f"ERROR | Context: {context} | Error: {type(error).__name__}: {error}")
    
    def log_performance(self, operation: str, duration: float, details: str = ''):
        """Log performance metrics"""
        self.logger.info(f"PERFORMANCE | Operation: {operation} | Duration: {duration:.3f}s | Details: {details}")
    
    def log_security_event(self, event: str, details: str = ''):
        """Log security-related events"""
        self.logger.warning(f"SECURITY_EVENT | Event: {event} | Details: {details}")
    
    def debug(self, message: str):
        """Debug log"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Info log"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Warning log"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Error log"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Critical log"""
        self.logger.critical(message)

def cleanup_old_logs(log_dir: str = 'logs', days_to_keep: int = 30):
    """
    Clean up old log files
    
    Args:
        log_dir: Directory containing log files
        days_to_keep: Number of days to keep log files
    """
    if not os.path.exists(log_dir):
        return
    
    import time
    current_time = time.time()
    cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
    
    logger = get_logger('log_cleanup')
    deleted_count = 0
    
    try:
        for filename in os.listdir(log_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(log_dir, filename)
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old log files")
    
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")

def get_log_files(log_dir: str = 'logs') -> list:
    """
    Get list of log files with their info
    
    Args:
        log_dir: Directory containing log files
    
    Returns:
        List of dictionaries with log file information
    """
    if not os.path.exists(log_dir):
        return []
    
    log_files = []
    
    for filename in os.listdir(log_dir):
        if filename.endswith('.log'):
            file_path = os.path.join(log_dir, filename)
            stat = os.stat(file_path)
            
            log_files.append({
                'filename': filename,
                'path': file_path,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'size_mb': round(stat.st_size / (1024 * 1024), 2)
            })
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return log_files

def read_log_file(file_path: str, lines: int = 100) -> list:
    """
    Read last N lines from log file
    
    Args:
        file_path: Path to log file
        lines: Number of lines to read from the end
    
    Returns:
        List of log lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
    
    except Exception as e:
        logger = get_logger('log_reader')
        logger.error(f"Error reading log file {file_path}: {e}")
        return []

# Initialize default logger for the module
_default_logger = None

def get_default_logger() -> PDVLogger:
    """Get the default PDV logger instance"""
    global _default_logger
    if _default_logger is None:
        _default_logger = PDVLogger()
    return _default_logger