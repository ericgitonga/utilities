"""
Setup tab UI for the Facebook Video Data Tool application with improved API testing.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

from ..constants import PAGE_ID_HELP_TEXT, TOKEN_HELP_TEXT, GOOGLE_CREDENTIALS_HELP_TEXT
from ..utils import get_logger
from .dialogs import HelpDialog
from ..api import FacebookAPI


class SetupTab:
    """Setup tab with authentication settings."""

    def __init__(self, parent, notebook, config, status_var):
        """
        Initialize setup tab.

        Args:
            parent: Parent frame
            notebook: Parent notebook
            config: Application configuration
            status_var: Status bar variable
        """
        self.parent = parent
        self.notebook = notebook
        self.config = config
        self.status_var = status_var
        self.logger = get_logger()

        # Create tab frame
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Setup")

        # Build UI
        self._build_ui()

        # Bind events
        self.tab.bind("<FocusOut>", self._on_focus_out)

    def _build_ui(self):
        """Build the tab UI."""
        # Facebook API Configuration
        fb_frame = ttk.LabelFrame(self.tab, text="Facebook API Configuration", padding=10)
        fb_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Page ID
        ttk.Label(fb_frame, text="Facebook Page ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.page_id_var = tk.StringVar(value=self.config.page_id)
        ttk.Entry(fb_frame, textvariable=self.page_id_var, width=50).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(fb_frame, text="(e.g., 'cocacola' or page numeric ID)").grid(row=0, column=2, sticky=tk.W, pady=5)

        # Page ID help button
        ttk.Button(fb_frame, text="?", width=2, command=self._show_page_id_help).grid(row=0, column=3, padx=5)

        # Access Token
        ttk.Label(fb_frame, text="Access Token:").grid(row=1, column=0, sticky=tk.W, pady=5)
        token_frame = ttk.Frame(fb_frame)
        token_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)

        self.access_token_var = tk.StringVar(value=self.config.access_token)
        self.token_entry = ttk.Entry(token_frame, textvariable=self.access_token_var, width=50, show="*")
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(token_frame, text="Show", command=self._toggle_token_visibility).pack(side=tk.LEFT, padx=5)

        # Load token from file option
        token_file_frame = ttk.Frame(fb_frame)
        token_file_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)

        self.token_from_file_var = tk.BooleanVar(value=self.config.token_from_file)
        ttk.Checkbutton(
            token_file_frame,
            text="Load token from file",
            variable=self.token_from_file_var,
            command=self._toggle_token_source,
        ).pack(side=tk.LEFT)

        self.token_path_var = tk.StringVar(value=self.config.token_path)
        self.token_file_entry = ttk.Entry(
            token_file_frame,
            textvariable=self.token_path_var,
            width=40,
            state=tk.NORMAL if self.config.token_from_file else tk.DISABLED,
        )
        self.token_file_entry.pack(side=tk.LEFT, padx=5)

        self.browse_token_btn = ttk.Button(
            token_file_frame,
            text="Browse...",
            command=self._browse_token_file,
            state=tk.NORMAL if self.config.token_from_file else tk.DISABLED,
        )
        self.browse_token_btn.pack(side=tk.LEFT)

        # Token help
        ttk.Button(fb_frame, text="Get Access Token Help", command=self._show_token_help).grid(
            row=3, column=1, sticky=tk.W, pady=5
        )

        # Video limit
        ttk.Label(fb_frame, text="Maximum Videos:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.max_videos_var = tk.IntVar(value=self.config.max_videos)
        ttk.Spinbox(fb_frame, from_=1, to=1000, textvariable=self.max_videos_var, width=10).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=5
        )

        # Google credentials
        google_frame = ttk.LabelFrame(self.tab, text="Google Sheets Configuration", padding=10)
        google_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        ttk.Label(google_frame, text="Credentials File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        cred_frame = ttk.Frame(google_frame)
        cred_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)

        self.credentials_path_var = tk.StringVar(value=self.config.credentials_path)
        ttk.Entry(cred_frame, textvariable=self.credentials_path_var, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(cred_frame, text="Browse...", command=self._browse_credentials_file).pack(side=tk.LEFT, padx=5)

        # Google credentials help
        ttk.Button(google_frame, text="Setup Google Credentials Help", command=self._show_google_credentials_help).grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        # Test connection buttons
        button_frame = ttk.Frame(self.tab)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Test Connection", command=self._test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Test API Versions", command=self._test_api_versions).pack(side=tk.LEFT, padx=5)

        # API version display
        version_frame = ttk.Frame(self.tab)
        version_frame.pack(pady=5)

        ttk.Label(version_frame, text="Current API Version:").pack(side=tk.LEFT)
        self.api_version_var = tk.StringVar(value=self._get_api_version())
        ttk.Label(version_frame, textvariable=self.api_version_var).pack(side=tk.LEFT, padx=5)

    def _get_api_version(self):
        """Extract API version from the base URL."""
        from ..constants import FB_API_BASE_URL

        if "v" in FB_API_BASE_URL:
            parts = FB_API_BASE_URL.split("/")
            for part in parts:
                if part.startswith("v"):
                    return part
        return "Unknown"

    def _toggle_token_visibility(self):
        """Toggle visibility of the token entry field."""
        if self.token_entry.cget("show") == "*":
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")

    def _toggle_token_source(self):
        """Toggle between direct token entry and file loading."""
        if self.token_from_file_var.get():
            self.token_entry.config(state=tk.DISABLED)
            self.token_file_entry.config(state=tk.NORMAL)
            self.browse_token_btn.config(state=tk.NORMAL)
        else:
            self.token_entry.config(state=tk.NORMAL)
            self.token_file_entry.config(state=tk.DISABLED)
            self.browse_token_btn.config(state=tk.DISABLED)

    def _browse_credentials_file(self):
        """Browse for Google API credentials file."""
        file_path = filedialog.askopenfilename(
            title="Select Google API Credentials JSON", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            self.credentials_path_var.set(file_path)
            os.environ["GOOGLE_CREDENTIALS_PATH"] = file_path

    def _browse_token_file(self):
        """Browse for token file."""
        file_path = filedialog.askopenfilename(
            title="Select Token File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        self.token_path_var.set(file_path)

        # Try to load the token from the file
        try:
            with open(file_path, "r") as f:
                token = f.read().strip()
                self.access_token_var.set(token)
            self.logger.log(f"Loaded token from {file_path}")
        except (IOError, OSError) as e:
            self.logger.log(f"Error loading token: {e}")
            messagebox.showerror("Error", f"Could not load token from file: {e}")

    def _show_page_id_help(self):
        """Show help dialog for finding page ID."""
        HelpDialog(self.parent, "Finding Your Page ID", PAGE_ID_HELP_TEXT)

    def _show_token_help(self):
        """Show help dialog for getting access token."""
        HelpDialog(self.parent, "Getting an Access Token", TOKEN_HELP_TEXT)

    def _show_google_credentials_help(self):
        """Show help dialog for setting up Google credentials."""
        HelpDialog(self.parent, "Google Sheets Setup", GOOGLE_CREDENTIALS_HELP_TEXT)

    def _test_connection(self):
        """Test the Facebook API connection."""
        page_id = self.page_id_var.get().strip()

        if not page_id:
            messagebox.showerror("Error", "Please enter a Page ID")
            return

        # Get access token
        access_token = self._get_access_token()
        if not access_token:
            return

        self.status_var.set("Testing connection...")
        self.logger.log("Testing connection to Facebook API...")

        # Run in a thread to avoid freezing UI
        threading.Thread(target=self._test_connection_thread, args=(page_id, access_token)).start()

    def _test_api_versions(self):
        """Test multiple Facebook API versions to find a working one."""
        page_id = self.page_id_var.get().strip()

        if not page_id:
            messagebox.showerror("Error", "Please enter a Page ID")
            return

        # Get access token
        access_token = self._get_access_token()
        if not access_token:
            return

        self.status_var.set("Testing API versions...")
        self.logger.log("Testing multiple Facebook API versions...")

        # Run in a thread to avoid freezing UI
        threading.Thread(target=self._test_api_versions_thread, args=(page_id, access_token)).start()

    def _test_connection_thread(self, page_id, access_token):
        """Thread for testing API connection."""
        try:
            # Initialize API with parent and status_var for updates
            fb_api = FacebookAPI(access_token, parent=self.parent, status_var=self.status_var)

            # Try to get a single video
            response = fb_api.get_page_videos(page_id, limit=1)

            # Check if response contains data
            if hasattr(response, "data") and len(response.data) > 0:
                self.logger.log("Connection successful! Found videos on the page.")
                messagebox.showinfo("Success", "Connected successfully to Facebook API!")
            elif hasattr(response, "data"):
                self.logger.log("Connection successful, but no videos found on this page.")
                messagebox.showinfo("Success", "Connected to Facebook API, but no videos found on this page.")
            else:
                self.logger.log(f"Connection error or invalid response: {response}")
                messagebox.showerror("Error", "Could not retrieve videos. Check your Page ID and Access Token.")

        except Exception as e:
            self.logger.log(f"Error testing connection: {e}")
            error_message = str(e)
            messagebox.showerror("Error", f"Connection failed: {error_message}")

        finally:
            self.status_var.set("Ready")

    def _test_api_versions_thread(self, page_id, access_token):
        """Thread for testing multiple API versions."""
        try:
            # Initialize API
            fb_api = FacebookAPI(access_token, parent=self.parent, status_var=self.status_var)

            # Test API versions
            success, version, message = fb_api.test_api_versions(page_id)

            if success:
                self.logger.log(f"API version test successful: {message}")

                # Update version display
                self.api_version_var.set(version)

                # Update constants file if available
                self._update_api_version_in_constants(version)

                messagebox.showinfo("Success", message)
            else:
                self.logger.log(f"API version test failed: {message}")
                messagebox.showerror("Error", message)

        except Exception as e:
            self.logger.log(f"Error testing API versions: {e}")
            messagebox.showerror("Error", f"Error testing API versions: {e}")

        finally:
            self.status_var.set("Ready")

    def _update_api_version_in_constants(self, version):
        """Update API version in constants file if possible."""
        try:
            constants_path = None

            # Try to locate the constants.py file
            import inspect
            import os
            from .. import constants

            constants_path = inspect.getfile(constants)
            self.logger.log(f"Found constants file at: {constants_path}")

            if constants_path and os.path.isfile(constants_path):
                with open(constants_path, "r") as f:
                    content = f.read()

                # Replace API base URL
                import re

                new_content = re.sub(
                    r'FB_API_BASE_URL\s*=\s*"[^"]*"',
                    f'FB_API_BASE_URL = "https://graph.facebook.com/{version}/"',
                    content,
                )

                if new_content != content:
                    with open(constants_path, "w") as f:
                        f.write(new_content)
                    self.logger.log(f"Updated API version in constants.py to {version}")
        except Exception as e:
            self.logger.log(f"Could not update API version in constants: {e}")
            # Non-critical error, so don't show to user

    def _get_access_token(self):
        """
        Get access token from UI or file.

        Returns:
            str: Access token or None if error
        """
        if self.token_from_file_var.get():
            token_path = self.token_path_var.get()
            if not token_path or not os.path.isfile(token_path):
                messagebox.showerror("Error", "Token file not found")
                return None

            try:
                with open(token_path, "r") as f:
                    token = f.read().strip()
                    if not token:
                        messagebox.showerror("Error", "Token file is empty")
                        return None
                    return token
            except (IOError, OSError) as e:
                messagebox.showerror("Error", f"Could not read token file: {e}")
                self.logger.log(f"Error loading token from file: {e}")
                return None
        else:
            token = self.access_token_var.get().strip()
            if not token:
                messagebox.showerror("Error", "Please enter an Access Token")
                return None
            return token

    def update_config(self):
        """Update configuration from UI values."""
        # Update the Pydantic config object through the property accessors
        self.config.page_id = self.page_id_var.get()
        self.config.token_from_file = self.token_from_file_var.get()
        self.config.token_path = self.token_path_var.get()
        self.config.access_token = self.access_token_var.get()

        # Safe conversion for max_videos with validation through the Pydantic model
        try:
            self.config.max_videos = int(self.max_videos_var.get())
        except (ValueError, TypeError):
            # If conversion fails, Pydantic will use the default value
            pass

        self.config.credentials_path = self.credentials_path_var.get()

        if self.config.credentials_path and os.path.isfile(self.config.credentials_path):
            os.environ["GOOGLE_CREDENTIALS_PATH"] = self.config.credentials_path

    def _on_focus_out(self, event=None):
        """Handle focus out event to update config."""
        self.update_config()
        self.config.save_settings()
