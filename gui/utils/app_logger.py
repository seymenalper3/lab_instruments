#!/usr/bin/env python3
"""
Centralized logging system for the GUI application
Provides file and console logging with rotation and filtering
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import queue
import threading


class QueueHandler(logging.Handler):
    """
    Custom handler that puts log records into a queue
    Used for real-time log display in GUI
    """
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            self.log_queue.put_nowait(self.format(record))
        except queue.Full:
            # If queue is full, remove oldest item and add new one
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(self.format(record))
            except:
                pass


class AppLogger:
    """
    Application-wide logging manager
    Handles file logging, console logging, and GUI queue logging
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure only one logger instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize logging system"""
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        # Create logs directory
        self.log_dir = Path('./logs')
        self.log_dir.mkdir(exist_ok=True)

        # Queue for GUI log display (max 1000 messages)
        self.gui_log_queue = queue.Queue(maxsize=1000)

        # Configure root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self.root_logger.handlers.clear()

        # Create formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )

        self.gui_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )

        # Setup handlers
        self._setup_file_handler()
        self._setup_console_handler()
        self._setup_gui_handler()

        # Log startup message
        logging.info("="*60)
        logging.info("Logging system initialized")
        logging.info(f"Log directory: {self.log_dir.absolute()}")
        logging.info("="*60)

    def _setup_file_handler(self):
        """Setup rotating file handler"""
        log_file = self.log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'

        # Rotating file handler (10 MB per file, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.detailed_formatter)
        self.root_logger.addHandler(file_handler)

        self.file_handler = file_handler

    def _setup_console_handler(self):
        """Setup console (stdout) handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console shows INFO and above
        console_handler.setFormatter(self.simple_formatter)
        self.root_logger.addHandler(console_handler)

        self.console_handler = console_handler

    def _setup_gui_handler(self):
        """Setup GUI queue handler for real-time display"""
        gui_handler = QueueHandler(self.gui_log_queue)
        gui_handler.setLevel(logging.DEBUG)  # GUI can show all levels
        gui_handler.setFormatter(self.gui_formatter)
        self.root_logger.addHandler(gui_handler)

        self.gui_handler = gui_handler

    def set_console_level(self, level: str):
        """
        Set console logging level

        Args:
            level: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        log_level = level_map.get(level.upper(), logging.INFO)
        self.console_handler.setLevel(log_level)
        logging.info(f"Console log level set to: {level.upper()}")

    def set_file_level(self, level: str):
        """
        Set file logging level

        Args:
            level: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        log_level = level_map.get(level.upper(), logging.DEBUG)
        self.file_handler.setLevel(log_level)
        logging.info(f"File log level set to: {level.upper()}")

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module

        Args:
            name: Module name (usually __name__)

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    def get_gui_queue(self) -> queue.Queue:
        """
        Get the queue for GUI log display

        Returns:
            Queue containing formatted log messages
        """
        return self.gui_log_queue

    def log_exception(self, logger: logging.Logger, message: str, exc_info=True):
        """
        Log an exception with full context

        Args:
            logger: Logger instance to use
            message: Context message
            exc_info: Whether to include exception info (default True)
        """
        logger.error(message, exc_info=exc_info)

    def log_device_command(self, device: str, command: str, response: Optional[str] = None):
        """
        Log a device command and response

        Args:
            device: Device name
            command: Command sent
            response: Response received (if any)
        """
        logger = logging.getLogger(f'device.{device}')
        if response is not None:
            logger.debug(f"CMD: {command} | RSP: {response}")
        else:
            logger.debug(f"CMD: {command}")

    def get_all_log_files(self) -> list:
        """
        Get list of all log files

        Returns:
            List of Path objects for log files
        """
        return sorted(self.log_dir.glob('app_*.log*'), reverse=True)

    def create_session_marker(self, message: str):
        """
        Create a visible marker in the logs

        Args:
            message: Marker message
        """
        logger = logging.getLogger('session')
        logger.info("="*60)
        logger.info(message)
        logger.info("="*60)


# Global instance
_app_logger = None
_logger_lock = threading.Lock()


def get_app_logger() -> AppLogger:
    """
    Get the global AppLogger instance
    Thread-safe singleton access

    Returns:
        AppLogger instance
    """
    global _app_logger
    if _app_logger is None:
        with _logger_lock:
            if _app_logger is None:
                _app_logger = AppLogger()
    return _app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger for a module

    Args:
        name: Module name (use __name__)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Module started")
    """
    app_logger = get_app_logger()
    return app_logger.get_logger(name)


# Initialize the logger when module is imported
get_app_logger()
