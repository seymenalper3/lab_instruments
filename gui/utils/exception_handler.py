#!/usr/bin/env python3
"""
Enhanced exception handling utilities for GUI application
Provides user-friendly error dialogs with detailed logging
"""
import tkinter as tk
from tkinter import messagebox
import traceback
import sys
from typing import Optional, Callable
from utils.app_logger import get_logger

logger = get_logger(__name__)


class ExceptionHandler:
    """
    Centralized exception handling with user notifications and logging
    """

    @staticmethod
    def handle_device_error(device_name: str, operation: str, exception: Exception,
                           parent_window: Optional[tk.Widget] = None,
                           show_dialog: bool = True) -> None:
        """
        Handle device-related errors with context

        Args:
            device_name: Name of the device (e.g., 'Keithley', 'Prodigit')
            operation: Operation that failed (e.g., 'connection', 'measurement')
            exception: The exception that occurred
            parent_window: Parent window for error dialog
            show_dialog: Whether to show error dialog to user
        """
        error_msg = f"Device '{device_name}' {operation} failed: {exception}"
        logger.error(error_msg, exc_info=True)

        if show_dialog:
            # Get the full traceback for the dialog
            tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            tb_str = ''.join(tb_lines)

            # Create user-friendly message
            user_message = (
                f"Error with {device_name}\n\n"
                f"Operation: {operation}\n"
                f"Error: {str(exception)}\n\n"
                f"Check the Debug Console tab for detailed information."
            )

            # Show error dialog
            messagebox.showerror(
                title=f"{device_name} Error",
                message=user_message,
                parent=parent_window
            )

    @staticmethod
    def handle_communication_error(device_name: str, command: str, exception: Exception,
                                  parent_window: Optional[tk.Widget] = None,
                                  show_dialog: bool = True) -> None:
        """
        Handle device communication errors

        Args:
            device_name: Name of the device
            command: SCPI command that failed
            exception: The exception that occurred
            parent_window: Parent window for error dialog
            show_dialog: Whether to show error dialog to user
        """
        error_msg = f"Communication error with '{device_name}' - Command: {command}"
        logger.error(error_msg, exc_info=True)
        logger.debug(f"Failed command details - Device: {device_name}, Command: '{command}'")

        if show_dialog:
            user_message = (
                f"Communication Error\n\n"
                f"Device: {device_name}\n"
                f"Command: {command}\n"
                f"Error: {str(exception)}\n\n"
                f"Possible causes:\n"
                f"• Device disconnected or powered off\n"
                f"• Communication timeout\n"
                f"• Invalid command format\n"
                f"• Device in wrong mode\n\n"
                f"Check the Debug Console for details."
            )

            messagebox.showerror(
                title="Communication Error",
                message=user_message,
                parent=parent_window
            )

    @staticmethod
    def handle_validation_error(field_name: str, value: any, constraint: str,
                                parent_window: Optional[tk.Widget] = None) -> None:
        """
        Handle input validation errors

        Args:
            field_name: Name of the field that failed validation
            value: The invalid value
            constraint: Description of the constraint that was violated
            parent_window: Parent window for error dialog
        """
        error_msg = f"Validation error - {field_name}: '{value}' violates constraint: {constraint}"
        logger.warning(error_msg)

        user_message = (
            f"Invalid Input\n\n"
            f"Field: {field_name}\n"
            f"Value: {value}\n"
            f"Requirement: {constraint}\n\n"
            f"Please correct the input and try again."
        )

        messagebox.showwarning(
            title="Invalid Input",
            message=user_message,
            parent=parent_window
        )

    @staticmethod
    def handle_file_error(operation: str, file_path: str, exception: Exception,
                         parent_window: Optional[tk.Widget] = None,
                         show_dialog: bool = True) -> None:
        """
        Handle file operation errors

        Args:
            operation: Operation that failed (e.g., 'read', 'write', 'parse')
            file_path: Path to the file
            exception: The exception that occurred
            parent_window: Parent window for error dialog
            show_dialog: Whether to show error dialog to user
        """
        error_msg = f"File {operation} error - Path: {file_path}"
        logger.error(error_msg, exc_info=True)

        if show_dialog:
            user_message = (
                f"File {operation.capitalize()} Error\n\n"
                f"File: {file_path}\n"
                f"Error: {str(exception)}\n\n"
                f"Possible causes:\n"
                f"• File not found or access denied\n"
                f"• Invalid file format\n"
                f"• Disk full or read-only\n\n"
                f"Check the Debug Console for details."
            )

            messagebox.showerror(
                title=f"File {operation.capitalize()} Error",
                message=user_message,
                parent=parent_window
            )

    @staticmethod
    def handle_unexpected_error(context: str, exception: Exception,
                               parent_window: Optional[tk.Widget] = None,
                               show_dialog: bool = True) -> None:
        """
        Handle unexpected/unknown errors

        Args:
            context: Description of what was being done
            exception: The exception that occurred
            parent_window: Parent window for error dialog
            show_dialog: Whether to show error dialog to user
        """
        error_msg = f"Unexpected error during {context}"
        logger.critical(error_msg, exc_info=True)

        if show_dialog:
            # Get the full traceback
            tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            tb_str = ''.join(tb_lines)

            user_message = (
                f"Unexpected Error\n\n"
                f"Context: {context}\n"
                f"Error: {str(exception)}\n\n"
                f"An unexpected error occurred. Please:\n"
                f"1. Check the Debug Console for details\n"
                f"2. Save the logs using the Debug Console\n"
                f"3. Report this issue if it persists\n"
            )

            messagebox.showerror(
                title="Unexpected Error",
                message=user_message,
                parent=parent_window
            )

    @staticmethod
    def create_safe_wrapper(func: Callable, context: str,
                           parent_window: Optional[tk.Widget] = None) -> Callable:
        """
        Create a wrapper that safely executes a function with error handling

        Args:
            func: Function to wrap
            context: Description of the function for error messages
            parent_window: Parent window for error dialogs

        Returns:
            Wrapped function with error handling

        Example:
            safe_connect = ExceptionHandler.create_safe_wrapper(
                self.connect,
                "device connection",
                self.root
            )
            safe_connect(config)
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ExceptionHandler.handle_unexpected_error(
                    context=context,
                    exception=e,
                    parent_window=parent_window
                )
                return None

        return wrapper


def setup_global_exception_handler(root_window: Optional[tk.Tk] = None):
    """
    Setup global exception handler for unhandled exceptions

    Args:
        root_window: Root Tk window for showing error dialogs
    """
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow KeyboardInterrupt to pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the exception
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        # Show error dialog if we have a root window
        if root_window:
            error_msg = (
                "A critical error occurred in the application.\n\n"
                f"Error: {exc_value}\n\n"
                "The error has been logged. Please:\n"
                "1. Save your work if possible\n"
                "2. Check the Debug Console\n"
                "3. Restart the application"
            )

            try:
                messagebox.showerror(
                    title="Critical Error",
                    message=error_msg,
                    parent=root_window
                )
            except:
                # If GUI is broken, at least print the error
                print(f"CRITICAL ERROR: {exc_value}")

    # Install the global exception handler
    sys.excepthook = handle_exception
    logger.info("Global exception handler installed")


# Example usage in controllers:
"""
from utils.exception_handler import ExceptionHandler

class MyController:
    def connect(self, config):
        try:
            # Connection code here
            self.interface.connect(config.host, config.port)
            logger.info(f"Connected successfully")
        except Exception as e:
            ExceptionHandler.handle_device_error(
                device_name="MyDevice",
                operation="connection",
                exception=e,
                parent_window=self.parent_frame
            )
            raise
"""
