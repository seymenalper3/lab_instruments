#!/usr/bin/env python3
"""
Main entry point for the modular GUI application
"""
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize logging system first
from utils.app_logger import get_logger, get_app_logger

logger = get_logger(__name__)

from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    try:
        logger.info("="*60)
        logger.info("Application starting...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info("="*60)

        app = MainWindow()
        app.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user")

    except Exception as e:
        logger.critical(f"Critical application error: {e}", exc_info=True)
        print(f"Application error: {e}")
        print("Check logs for detailed error information")
        sys.exit(1)

    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()