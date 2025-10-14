#!/usr/bin/env python3
"""
Debug Console Tab - Real-time log viewer for the GUI application
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import queue
from datetime import datetime
from pathlib import Path


class DebugConsoleTab:
    """Debug console tab for viewing application logs in real-time"""

    def __init__(self, parent, log_queue):
        """
        Initialize debug console tab

        Args:
            parent: Parent notebook widget
            log_queue: Queue containing log messages from AppLogger
        """
        self.parent = parent
        self.log_queue = log_queue
        self.running = False
        self.update_thread = None
        self.paused = False
        self.auto_scroll = True
        self.log_level_filter = 'ALL'

        # Create main frame
        self.frame = ttk.Frame(parent)

        # Create GUI elements
        self._create_gui()

        # Start log update thread
        self.start_monitoring()

    def _create_gui(self):
        """Create the debug console GUI"""
        # Top control panel
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=5, pady=5)

        # Left side controls
        left_controls = ttk.Frame(control_frame)
        left_controls.pack(side='left', fill='x', expand=True)

        # Log level filter
        ttk.Label(left_controls, text="Filter Level:").pack(side='left', padx=(0, 5))
        self.level_var = tk.StringVar(value='ALL')
        level_combo = ttk.Combobox(
            left_controls,
            textvariable=self.level_var,
            values=['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            state='readonly',
            width=10
        )
        level_combo.pack(side='left', padx=(0, 10))
        level_combo.bind('<<ComboboxSelected>>', self._on_level_filter_changed)

        # Pause/Resume button
        self.pause_button = ttk.Button(
            left_controls,
            text="⏸ Pause",
            command=self._toggle_pause,
            width=10
        )
        self.pause_button.pack(side='left', padx=(0, 5))

        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_check = ttk.Checkbutton(
            left_controls,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll
        )
        auto_scroll_check.pack(side='left', padx=(0, 10))

        # Right side controls
        right_controls = ttk.Frame(control_frame)
        right_controls.pack(side='right')

        # Clear button
        ttk.Button(
            right_controls,
            text="Clear",
            command=self._clear_console,
            width=10
        ).pack(side='left', padx=(0, 5))

        # Save button
        ttk.Button(
            right_controls,
            text="Save to File",
            command=self._save_to_file,
            width=12
        ).pack(side='left', padx=(0, 5))

        # Copy button
        ttk.Button(
            right_controls,
            text="Copy All",
            command=self._copy_to_clipboard,
            width=10
        ).pack(side='left')

        # Separator
        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', padx=5)

        # Log display area with scrollbar
        log_frame = ttk.Frame(self.frame)
        log_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create scrolled text widget
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=('Consolas', 9) if tk.sys.platform == 'win32' else ('Courier', 9),
            state='disabled',
            background='#1e1e1e',
            foreground='#d4d4d4'
        )
        self.log_text.pack(fill='both', expand=True)

        # Configure text tags for different log levels with colors
        self.log_text.tag_config('DEBUG', foreground='#808080')      # Gray
        self.log_text.tag_config('INFO', foreground='#4ec9b0')       # Cyan
        self.log_text.tag_config('WARNING', foreground='#ffd700')    # Gold
        self.log_text.tag_config('ERROR', foreground='#f48771')      # Light Red
        self.log_text.tag_config('CRITICAL', foreground='#ff0000', font=('Courier', 9, 'bold'))  # Red Bold

        # Status bar
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill='x', padx=5, pady=(0, 5))

        self.status_label = ttk.Label(
            status_frame,
            text="Debug Console Active | Lines: 0",
            relief='sunken'
        )
        self.status_label.pack(side='left', fill='x', expand=True)

        # Add initial welcome message
        self._add_welcome_message()

    def _add_welcome_message(self):
        """Add welcome message to console"""
        welcome = f"""
{'='*80}
Debug Console - Real-time Application Logs
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

"""
        self.log_text.config(state='normal')
        self.log_text.insert('end', welcome, 'INFO')
        self.log_text.config(state='disabled')

    def _toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            self.pause_button.config(text="▶ Resume")
            self._update_status("PAUSED")
        else:
            self.pause_button.config(text="⏸ Pause")
            self._update_status("Active")

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll"""
        self.auto_scroll = self.auto_scroll_var.get()

    def _on_level_filter_changed(self, event=None):
        """Handle log level filter change"""
        self.log_level_filter = self.level_var.get()
        self._update_status(f"Filter: {self.log_level_filter}")

    def _clear_console(self):
        """Clear the console"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')
        self._add_welcome_message()
        self._update_status("Console cleared")

    def _save_to_file(self):
        """Save console contents to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f'debug_console_{timestamp}.log'

            filepath = filedialog.asksaveasfilename(
                defaultextension='.log',
                filetypes=[('Log files', '*.log'), ('Text files', '*.txt'), ('All files', '*.*')],
                initialfile=default_filename
            )

            if filepath:
                content = self.log_text.get('1.0', 'end-1c')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Logs saved to:\n{filepath}")
                self._update_status(f"Saved to {Path(filepath).name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def _copy_to_clipboard(self):
        """Copy all console contents to clipboard"""
        try:
            content = self.log_text.get('1.0', 'end-1c')
            self.frame.clipboard_clear()
            self.frame.clipboard_append(content)
            self._update_status("Copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard:\n{e}")

    def _update_status(self, message: str = None):
        """Update status bar"""
        line_count = int(self.log_text.index('end-1c').split('.')[0]) - 1

        if message:
            status_text = f"Debug Console {message} | Lines: {line_count}"
        else:
            status_text = f"Debug Console Active | Lines: {line_count}"

        self.status_label.config(text=status_text)

    def _get_log_level_from_message(self, message: str) -> str:
        """Extract log level from message"""
        for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
            if level in message:
                return level
        return 'INFO'

    def _should_display_message(self, message: str) -> bool:
        """Check if message should be displayed based on filter"""
        if self.log_level_filter == 'ALL':
            return True

        log_level = self._get_log_level_from_message(message)
        return log_level == self.log_level_filter

    def start_monitoring(self):
        """Start the log monitoring thread"""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

    def stop_monitoring(self):
        """Stop the log monitoring thread"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)

    def _update_loop(self):
        """Background thread that reads from log queue and updates GUI"""
        while self.running:
            try:
                # Process all available messages (up to 100 at a time to avoid GUI freezing)
                messages_processed = 0
                while messages_processed < 100 and not self.log_queue.empty():
                    try:
                        message = self.log_queue.get_nowait()

                        # Skip if paused or filtered
                        if self.paused or not self._should_display_message(message):
                            continue

                        # Schedule GUI update on main thread
                        self.frame.after(0, self._add_log_message, message)
                        messages_processed += 1

                    except queue.Empty:
                        break

                # Sleep briefly to avoid busy-waiting
                threading.Event().wait(0.1)

            except Exception as e:
                # Log errors but keep running
                print(f"Debug console update error: {e}")
                threading.Event().wait(1.0)

    def _add_log_message(self, message: str):
        """Add a log message to the text widget (must be called from main thread)"""
        try:
            # Determine log level for coloring
            log_level = self._get_log_level_from_message(message)

            # Enable editing
            self.log_text.config(state='normal')

            # Add message with appropriate tag
            self.log_text.insert('end', message + '\n', log_level)

            # Limit buffer size to prevent memory issues (keep last 10000 lines)
            line_count = int(self.log_text.index('end-1c').split('.')[0])
            if line_count > 10000:
                self.log_text.delete('1.0', f'{line_count - 10000}.0')

            # Auto-scroll to bottom if enabled
            if self.auto_scroll:
                self.log_text.see('end')

            # Disable editing
            self.log_text.config(state='disabled')

            # Update status periodically (every 20 messages)
            if line_count % 20 == 0:
                self._update_status()

        except Exception as e:
            print(f"Error adding log message: {e}")
