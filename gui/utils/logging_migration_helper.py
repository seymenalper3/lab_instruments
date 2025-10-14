#!/usr/bin/env python3
"""
Helper script to demonstrate migrating from print() to logging

This shows the pattern for updating code to use proper logging
"""
from utils.app_logger import get_logger

# Example of how to use logging in your controllers:

# At the top of your controller file, add:
# from utils.app_logger import get_logger
# logger = get_logger(__name__)

# Then replace print statements as follows:

# OLD: print("Starting operation...")
# NEW: logger.info("Starting operation...")

# OLD: print(f"Error: {e}")
# NEW: logger.error(f"Error: {e}", exc_info=True)  # exc_info=True adds stack trace

# OLD: print(f"DEBUG: Value is {value}")
# NEW: logger.debug(f"Value is {value}")

# OLD: print(f"Warning: unusual condition")
# NEW: logger.warning("Warning: unusual condition")

# For device commands, use the special device command logger:
# from utils.app_logger import get_app_logger
# app_logger = get_app_logger()
# app_logger.log_device_command('keithley', command, response)


# Logging Levels Guide:
# - DEBUG: Detailed information for diagnosing problems (verbose)
# - INFO: General information about program execution
# - WARNING: Something unexpected but not an error
# - ERROR: A serious problem occurred
# - CRITICAL: A very serious error, program may not continue

# Best practices:
# 1. Use f-strings for formatting: logger.info(f"Value: {value}")
# 2. Include context: logger.error(f"Failed to connect to {device_name}: {e}")
# 3. Use exc_info=True for errors to include stack traces
# 4. Log entry/exit of important operations
# 5. Log state changes (mode switches, connections, etc.)


def example_migration():
    """Example showing before and after"""
    logger = get_logger(__name__)

    # BEFORE (using print)
    """
    def connect(self, host):
        print("Connecting to device...")
        try:
            self.connection = create_connection(host)
            print(f"Connected to {host}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    """

    # AFTER (using logging)
    """
    def connect(self, host):
        logger.info(f"Connecting to device at {host}...")
        try:
            self.connection = create_connection(host)
            logger.info(f"Successfully connected to {host}")
            return True
        except Exception as e:
            logger.error(f"Connection failed to {host}: {e}", exc_info=True)
            return False
    """


if __name__ == "__main__":
    print(__doc__)
