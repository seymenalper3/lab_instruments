# Debugging Guide

## Overview

The GUI application now includes a comprehensive debugging system to make troubleshooting easier. This guide explains how to use the debugging features effectively.

## Features

### 1. Debug Console Tab

A real-time log viewer integrated into the GUI.

**Location:** Last tab in the main window labeled "Debug Console"

**Features:**
- Real-time display of all application logs
- Color-coded messages by severity:
  - Gray: DEBUG - Detailed diagnostic information
  - Cyan: INFO - General information
  - Gold: WARNING - Warning messages
  - Light Red: ERROR - Error messages
  - Red Bold: CRITICAL - Critical errors
- Filter logs by level (ALL, DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Pause/Resume log updates
- Auto-scroll toggle
- Clear console
- Save logs to file
- Copy all logs to clipboard

**Usage:**
1. Open the application
2. Click on the "Debug Console" tab
3. Logs appear in real-time as you use the application
4. Use filters to focus on specific log levels
5. Save logs before closing if you need to report issues

### 2. File Logging

All logs are automatically saved to files for later review.

**Location:** `./logs/` directory

**File Format:** `app_YYYYMMDD.log`

**Features:**
- Automatic log rotation (10 MB per file, keeps 5 backups)
- Detailed format includes: timestamp, log level, module name, line number, message
- Survives application restarts
- Can be reviewed with any text editor

**Example log entry:**
```
2025-01-15 14:23:45 | INFO     | gui.main_window:23 | Initializing main window...
2025-01-15 14:23:46 | DEBUG    | controllers.keithley_controller:107 | Switching to Power Supply mode...
2025-01-15 14:23:47 | ERROR    | controllers.keithley_controller:155 | Failed to switch to Power Supply mode: timeout
```

### 3. Centralized Logging System

All modules use a centralized logging system instead of scattered print statements.

**Benefits:**
- Consistent log format across all modules
- Log levels allow filtering important vs. verbose messages
- Logs include source location (file and line number)
- Better error tracking with full stack traces
- Can adjust verbosity without code changes

### 4. Enhanced Exception Handling

Improved error reporting with context and user-friendly dialogs.

**Features:**
- Detailed error context (device name, operation, parameters)
- Full stack traces logged for debugging
- User-friendly error dialogs with troubleshooting hints
- Categorized errors (device, communication, file, validation)
- Automatic logging of all exceptions

**Example:**
When a device connection fails, you get:
- A user-friendly dialog explaining the problem
- Suggestions for fixing the issue
- Full technical details logged to the Debug Console
- Stack trace saved to the log file

## How to Use for Debugging

### Basic Workflow

1. **Reproduce the Issue:**
   - Open the Debug Console tab
   - Set filter to "ALL" to see everything
   - Perform the action that causes the problem
   - Watch the Debug Console for errors

2. **Analyze the Logs:**
   - Look for ERROR or CRITICAL level messages
   - Check timestamps to understand the sequence of events
   - Read the context information (device names, operations, values)

3. **Save Evidence:**
   - Click "Save to File" in Debug Console
   - Or navigate to `./logs/` directory
   - Include log files when reporting issues

### Common Debugging Scenarios

#### Device Connection Issues

**What to check:**
1. Look for connection-related errors in Debug Console
2. Check if device communication commands are being sent
3. Verify device responses (or lack thereof)

**Example log pattern:**
```
INFO | Connecting to device at 192.168.1.100...
DEBUG | CMD: *IDN? | RSP: <no response>
ERROR | Connection failed to 192.168.1.100: timeout
```

#### Measurement Problems

**What to check:**
1. Filter for the specific device name
2. Look for measurement command failures
3. Check if device is in correct mode

**Example log pattern:**
```
DEBUG | Device in Power Supply mode
DEBUG | CMD: MEAS:VOLT? | RSP: +12.345
DEBUG | CMD: MEAS:CURR? | RSP: +0.123
INFO | Measurement: V=12.345V I=0.123A
```

#### Application Crashes

**What to check:**
1. Look for CRITICAL level messages
2. Check the last few log entries before crash
3. Review full stack traces in log file

**Stack traces show:**
- Exact line where error occurred
- Full call chain leading to the error
- Variable values at time of error

### Advanced Debugging

#### Adjusting Log Levels

You can adjust what gets logged by modifying log levels:

```python
from utils.app_logger import get_app_logger

app_logger = get_app_logger()
app_logger.set_console_level('DEBUG')  # Show everything in console
app_logger.set_file_level('INFO')      # Only log INFO and above to file
```

#### Custom Logging in Your Code

When adding new features, use proper logging:

```python
from utils.app_logger import get_logger

logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed diagnostic info")
logger.info("General information")
logger.warning("Something unexpected happened")
logger.error("An error occurred", exc_info=True)  # Include stack trace
logger.critical("Critical error, application may fail")

# Log device commands
from utils.app_logger import get_app_logger
app_logger = get_app_logger()
app_logger.log_device_command('keithley', '*IDN?', 'KEITHLEY,2281S,...')
```

## Troubleshooting Common Issues

### Debug Console Not Showing Logs

**Possible causes:**
1. Log level filter is too restrictive
2. Console is paused
3. Application just started (logs appear after initialization)

**Solutions:**
- Set filter to "ALL"
- Click "Resume" if paused
- Wait a few seconds for initialization

### Log Files Getting Too Large

**Automatic handling:**
- Files automatically rotate at 10 MB
- Keeps 5 most recent backups
- Old logs are automatically deleted

**Manual cleanup:**
- Navigate to `./logs/` directory
- Delete old `app_*.log.*` backup files
- Keep the main `app_YYYYMMDD.log` files

### Performance Impact

**Impact:**
- Minimal performance overhead
- File logging is buffered
- GUI updates are throttled (max 100 messages at once)

**If experiencing slowdown:**
- Reduce log level to WARNING or ERROR
- Pause Debug Console when not needed
- Clear Debug Console periodically

## Best Practices

1. **Always check Debug Console first** when investigating issues
2. **Save logs before closing** the application if you encountered errors
3. **Include log files** when reporting bugs
4. **Use appropriate log levels** when adding your own logging
5. **Don't disable logging** even if it seems verbose - you can filter instead

## Log Levels Guide

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Detailed diagnostic information | "Sending command to device", "Received response: ..." |
| INFO | General informational messages | "Device connected", "Measurement complete" |
| WARNING | Unexpected but handled situations | "Retry attempt 2/3", "Using fallback method" |
| ERROR | Errors that don't crash the app | "Failed to read measurement", "Connection timeout" |
| CRITICAL | Serious errors that may crash | "Cannot initialize GUI", "Fatal device error" |

## Migration Guide for Developers

If you're updating old code that uses `print()`, here's how to convert:

### Before:
```python
print("Connecting to device...")
print(f"Error: {e}")
print(f"DEBUG: value is {x}")
```

### After:
```python
from utils.app_logger import get_logger
logger = get_logger(__name__)

logger.info("Connecting to device...")
logger.error(f"Error: {e}", exc_info=True)
logger.debug(f"value is {x}")
```

See `utils/logging_migration_helper.py` for more examples and patterns.

## Support

For questions or issues with the debugging system:
1. Check this guide
2. Review example code in `utils/logging_migration_helper.py`
3. Check the Debug Console for error messages
4. Save and review log files in `./logs/`
