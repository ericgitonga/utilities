import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import pandas as pd
import json
from datetime import datetime
import sys

# Import the fbvdata module
try:
    import fbvdata
except ImportError:
    # If the script is running from a different directory, add the current directory to sys.path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import fbvdata


class FacebookVideoDataApp:
    """GUI Application for Facebook Video Data Retrieval"""

    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Video Data Retrieval")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)

        # Set icon if available
        try:
            self.root.iconbitmap("fbv_icon.ico")
        except tk.TclError:
            pass  # Icon file not found, use default

        # Variables
        self.page_id_var = tk.StringVar()
        self.access_token_var = tk.StringVar()
        self.token_from_file_var = tk.BooleanVar(value=False)
        self.max_videos_var = tk.IntVar(value=25)
        self.export_format_var = tk.StringVar(value="CSV")
        self.spreadsheet_name_var = tk.StringVar(value="Facebook Video Data")
        self.worksheet_name_var = tk.StringVar(value="Video Data")
        self.output_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Documents"))

        self.credentials_path_var = tk.StringVar()
        self.token_path_var = tk.StringVar()

        # Main container with padding
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)
        self.export_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.setup_tab, text="Setup")
        self.notebook.add(self.data_tab, text="Video Data")
        self.notebook.add(self.export_tab, text="Export")
        self.notebook.add(self.log_tab, text="Log")

        # Build interface
        self._build_setup_tab()
        self._build_data_tab()
        self._build_export_tab()
        self._build_log_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Initialize data
        self.video_data = []
        self.fb_api = None

        # Load settings
        self._load_settings()

        # Config change tracking for auto-save
        self.setup_tab.bind("<FocusOut>", self._save_settings)
        self.export_tab.bind("<FocusOut>", self._save_settings)

    def _build_setup_tab(self):
        """Build the setup tab with authentication settings"""
        setup_frame = ttk.LabelFrame(self.setup_tab, text="Facebook API Configuration", padding=10)
        setup_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Page ID
        ttk.Label(setup_frame, text="Facebook Page ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(setup_frame, textvariable=self.page_id_var, width=50).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )
        ttk.Label(setup_frame, text="(e.g., 'cocacola' or page numeric ID)").grid(row=0, column=2, sticky=tk.W, pady=5)

        # Page ID help button
        ttk.Button(setup_frame, text="?", width=2, command=self._show_page_id_help).grid(row=0, column=3, padx=5)

        # Access Token
        ttk.Label(setup_frame, text="Access Token:").grid(row=1, column=0, sticky=tk.W, pady=5)
        token_frame = ttk.Frame(setup_frame)
        token_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)

        self.token_entry = ttk.Entry(token_frame, textvariable=self.access_token_var, width=50, show="*")
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(token_frame, text="Show", command=self._toggle_token_visibility).pack(side=tk.LEFT, padx=5)

        # Load token from file option
        token_file_frame = ttk.Frame(setup_frame)
        token_file_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)

        ttk.Checkbutton(
            token_file_frame,
            text="Load token from file",
            variable=self.token_from_file_var,
            command=self._toggle_token_source,
        ).pack(side=tk.LEFT)

        self.token_file_entry = ttk.Entry(
            token_file_frame, textvariable=self.token_path_var, width=40, state=tk.DISABLED
        )
        self.token_file_entry.pack(side=tk.LEFT, padx=5)

        self.browse_token_btn = ttk.Button(
            token_file_frame, text="Browse...", command=self._browse_token_file, state=tk.DISABLED
        )
        self.browse_token_btn.pack(side=tk.LEFT)

        # Token help
        ttk.Button(setup_frame, text="Get Access Token Help", command=self._show_token_help).grid(
            row=3, column=1, sticky=tk.W, pady=5
        )

        # Video limit
        ttk.Label(setup_frame, text="Maximum Videos:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(setup_frame, from_=1, to=100, textvariable=self.max_videos_var, width=10).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=5
        )

        # Google credentials
        google_frame = ttk.LabelFrame(self.setup_tab, text="Google Sheets Configuration", padding=10)
        google_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        ttk.Label(google_frame, text="Credentials File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        cred_frame = ttk.Frame(google_frame)
        cred_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W + tk.E, pady=5)

        ttk.Entry(cred_frame, textvariable=self.credentials_path_var, width=50).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(cred_frame, text="Browse...", command=self._browse_credentials_file).pack(side=tk.LEFT, padx=5)

        # Google credentials help
        ttk.Button(google_frame, text="Setup Google Credentials Help", command=self._show_google_credentials_help).grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        # Test button
        ttk.Button(self.setup_tab, text="Test Connection", command=self._test_connection).pack(pady=10)

    def _build_data_tab(self):
        """Build the data tab with treeview for displaying video data"""
        # Control frame
        control_frame = ttk.Frame(self.data_tab, padding=5)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(control_frame, text="Fetch Video Data", command=self._fetch_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Data", command=self._clear_data).pack(side=tk.LEFT, padx=5)

        # Create Treeview with scrollbars
        tree_frame = ttk.Frame(self.data_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Create horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Create Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("title", "created", "views", "comments", "likes", "shares"),
            show="headings",
            selectmode="browse",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        # Configure scrollbars
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Define columns
        self.tree.heading("title", text="Title")
        self.tree.heading("created", text="Created Date")
        self.tree.heading("views", text="Views")
        self.tree.heading("comments", text="Comments")
        self.tree.heading("likes", text="Likes")
        self.tree.heading("shares", text="Shares")

        # Set column widths
        self.tree.column("title", width=200, minwidth=100)
        self.tree.column("created", width=150, minwidth=100)
        self.tree.column("views", width=80, minwidth=50)
        self.tree.column("comments", width=80, minwidth=50)
        self.tree.column("likes", width=80, minwidth=50)
        self.tree.column("shares", width=80, minwidth=50)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Double-click to view details
        self.tree.bind("<Double-1>", self._show_video_details)

        # Stats frame
        stats_frame = ttk.LabelFrame(self.data_tab, text="Statistics", padding=5)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        self.stats_label = ttk.Label(stats_frame, text="No data loaded")
        self.stats_label.pack(pady=5)

    def _build_export_tab(self):
        """Build the export tab with export options"""
        export_frame = ttk.LabelFrame(self.export_tab, text="Export Options", padding=10)
        export_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Export format
        ttk.Label(export_frame, text="Export Format:").grid(row=0, column=0, sticky=tk.W, pady=5)

        format_frame = ttk.Frame(export_frame)
        format_frame.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Radiobutton(
            format_frame, text="CSV", variable=self.export_format_var, value="CSV", command=self._toggle_export_options
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            format_frame,
            text="Google Sheet",
            variable=self.export_format_var,
            value="Google",
            command=self._toggle_export_options,
        ).pack(side=tk.LEFT, padx=5)

        # Google Sheets options (conditionally enabled)
        self.google_frame = ttk.Frame(export_frame)
        self.google_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E, pady=5)

        ttk.Label(self.google_frame, text="Spreadsheet Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.google_frame, textvariable=self.spreadsheet_name_var, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(self.google_frame, text="Worksheet Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.google_frame, textvariable=self.worksheet_name_var, width=40).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )

        # Output path for CSV
        self.csv_frame = ttk.Frame(export_frame)
        self.csv_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W + tk.E, pady=5)

        ttk.Label(self.csv_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)

        path_frame = ttk.Frame(self.csv_frame)
        path_frame.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)

        ttk.Entry(path_frame, textvariable=self.output_path_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse...", command=self._browse_output_path).pack(side=tk.LEFT, padx=5)

        # Initial toggle state
        self._toggle_export_options()

        # Export button
        ttk.Button(self.export_tab, text="Export Data", command=self._export_data).pack(pady=10)

    def _build_log_tab(self):
        """Build the log tab with scrollable text area"""
        log_frame = ttk.Frame(self.log_tab, padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create text area with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Buttons
        button_frame = ttk.Frame(self.log_tab)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Log", command=self._save_log).pack(side=tk.LEFT, padx=5)

    def _toggle_token_visibility(self):
        """Toggle visibility of the token entry field"""
        if self.token_entry.cget("show") == "*":
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")

    def _toggle_token_source(self):
        """Toggle between direct token entry and file loading"""
        if self.token_from_file_var.get():
            self.token_entry.config(state=tk.DISABLED)
            self.token_file_entry.config(state=tk.NORMAL)
            self.browse_token_btn.config(state=tk.NORMAL)
        else:
            self.token_entry.config(state=tk.NORMAL)
            self.token_file_entry.config(state=tk.DISABLED)
            self.browse_token_btn.config(state=tk.DISABLED)

    def _toggle_export_options(self):
        """Toggle between CSV and Google Sheet export options"""
        if self.export_format_var.get() == "CSV":
            for child in self.google_frame.winfo_children():
                child.config(state=tk.DISABLED)
            for child in self.csv_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        subchild.config(state=tk.NORMAL)
                else:
                    child.config(state=tk.NORMAL)
        else:  # Google
            for child in self.google_frame.winfo_children():
                child.config(state=tk.NORMAL)
            for child in self.csv_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        subchild.config(state=tk.DISABLED)
                else:
                    child.config(state=tk.DISABLED)

    def _browse_credentials_file(self):
        """Browse for Google API credentials file"""
        file_path = filedialog.askopenfilename(
            title="Select Google API Credentials JSON", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            self.credentials_path_var.set(file_path)
            os.environ["GOOGLE_CREDENTIALS_PATH"] = file_path

    def _browse_token_file(self):
        """Browse for token file"""
        file_path = filedialog.askopenfilename(
            title="Select Token File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.token_path_var.set(file_path)
            # Try to load the token from the file
            try:
                with open(file_path, "r") as f:
                    token = f.read().strip()
                    self.access_token_var.set(token)
                self._log(f"Loaded token from {file_path}")
            except (IOError, OSError) as e:
                self._log(f"Error loading token: {e}")
                messagebox.showerror("Error", f"Could not load token from file: {e}")

    def _browse_output_path(self):
        """Browse for output directory"""
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_path_var.set(dir_path)

    def _show_page_id_help(self):
        """Show help dialog for finding page ID"""
        help_text = (
            "To find your Facebook Page ID:\n\n"
            "1. Go to your Facebook Page\n"
            "2. Look at the URL. If it's in the format:\n"
            "   https://www.facebook.com/YourPageName/\n"
            "   Then 'YourPageName' is your Page ID\n\n"
            "3. If you need the numeric ID, use Facebook's Graph API Explorer\n"
            "   and query for 'me' with a Page token to see your page's numeric ID."
        )
        messagebox.showinfo("Finding Your Page ID", help_text)

    def _show_token_help(self):
        """Show help dialog for getting access token"""
        help_text = (
            "To get a Facebook API Access Token:\n\n"
            "1. Go to developers.facebook.com and log in\n"
            "2. Create a new App if you don't have one\n"
            "3. Go to Tools & Support > Graph API Explorer\n"
            "4. Select your App from the dropdown\n"
            "5. Click 'Generate Access Token'\n"
            "6. Make sure to select the following permissions:\n"
            "   - pages_read_engagement\n"
            "   - pages_show_list\n"
            "   - pages_read_user_content\n"
            "7. Click 'Generate Access Token' and copy the token\n\n"
            "Note: For a longer-lived token, use the Access Token Debugger tool."
        )
        messagebox.showinfo("Getting an Access Token", help_text)

    def _show_google_credentials_help(self):
        """Show help dialog for setting up Google credentials"""
        help_text = (
            "To set up Google Sheets integration:\n\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Create a new project\n"
            "3. Go to 'APIs & Services' > 'Library'\n"
            "4. Enable 'Google Sheets API' and 'Google Drive API'\n"
            "5. Go to 'APIs & Services' > 'Credentials'\n"
            "6. Click 'Create Credentials' > 'Service account'\n"
            "7. Fill in service account details and grant 'Editor' role\n"
            "8. Create a JSON key and download it\n"
            "9. Select this JSON file in the Credentials File field\n"
            "10. If using an existing sheet, share it with the service account email address"
        )
        messagebox.showinfo("Google Sheets Setup", help_text)

    def _test_connection(self):
        """Test the Facebook API connection"""
        page_id = self.page_id_var.get().strip()

        if not page_id:
            messagebox.showerror("Error", "Please enter a Page ID")
            return

        # Get access token
        access_token = self._get_access_token()
        if not access_token:
            return

        self.status_var.set("Testing connection...")
        self._log("Testing connection to Facebook API...")

        # Run in a thread to avoid freezing UI
        threading.Thread(target=self._test_connection_thread, args=(page_id, access_token)).start()

    def _test_connection_thread(self, page_id, access_token):
        """Thread for testing API connection"""
        try:
            # Initialize API
            self.fb_api = fbvdata.FacebookAPI(access_token)

            # Try to get a single video
            result = self.fb_api.get_page_videos(page_id, limit=1)

            if result and "data" in result:
                if len(result["data"]) > 0:
                    self._log("Connection successful! Found videos on the page.")
                    self.root.after(
                        0, lambda: messagebox.showinfo("Success", "Connected successfully to Facebook API!")
                    )
                else:
                    self._log("Connection successful, but no videos found on this page.")
                    self.root.after(
                        0,
                        lambda: messagebox.showinfo(
                            "Success", "Connected to Facebook API, but no videos found on this page."
                        ),
                    )
            else:
                self._log(f"Connection error or invalid response: {result}")
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Error", "Could not retrieve videos. Check your Page ID and Access Token."
                    ),
                )

        except Exception as e:
            self._log(f"Error testing connection: {e}")
            error_message = str(e)  # Capture the error message
            self.root.after(0, lambda: messagebox.showerror("Error", f"Connection failed: {error_message}"))

        finally:
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def _fetch_data(self):
        """Fetch video data from Facebook"""
        page_id = self.page_id_var.get().strip()
        max_videos = self.max_videos_var.get()

        if not page_id:
            messagebox.showerror("Error", "Please enter a Page ID")
            return

        # Get access token
        access_token = self._get_access_token()
        if not access_token:
            return

        self.status_var.set("Fetching data...")
        self._log(f"Fetching video data for Page ID: {page_id} (max: {max_videos} videos)...")

        # Clear previous data
        self._clear_data()

        # Run in a thread to avoid freezing UI
        threading.Thread(target=self._fetch_data_thread, args=(page_id, access_token, max_videos)).start()

    def _fetch_data_thread(self, page_id, access_token, max_videos):
        """Thread for fetching video data"""
        try:
            # Get video data
            self.video_data = fbvdata.get_all_facebook_video_data(page_id, access_token, max_videos)

            # Update UI with results
            self.root.after(0, self._update_data_display)

        except Exception as e:
            self._log(f"Error fetching data: {e}")
            error_message = str(e)  # Capture the error message
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch data: {error_message}"))
            self.root.after(0, lambda: self.status_var.set("Error fetching data"))
            return

        self.root.after(0, lambda: self.status_var.set(f"Fetched {len(self.video_data)} videos"))

    def _update_data_display(self):
        """Update the treeview with fetched data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.video_data:
            self._log("No videos found.")
            self.stats_label.configure(text="No videos found")
            return

        # Add data to treeview
        for i, video in enumerate(self.video_data):
            title = video.get("title", "Untitled")
            if not title:
                title = video.get("description", "Untitled")[:50] + "..." if video.get("description") else "Untitled"

            created_time = video.get("created_time", "")
            if created_time:
                try:
                    created_time = pd.to_datetime(created_time).strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass

            # Insert data into tree
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    title,
                    created_time,
                    video.get("views", 0),
                    video.get("comments_count", 0),
                    video.get("likes_count", 0),
                    video.get("shares_count", 0),
                ),
            )

        # Calculate and display statistics
        total_videos = len(self.video_data)
        total_views = sum(video.get("views", 0) for video in self.video_data)
        total_comments = sum(video.get("comments_count", 0) for video in self.video_data)
        total_likes = sum(video.get("likes_count", 0) for video in self.video_data)
        total_shares = sum(video.get("shares_count", 0) for video in self.video_data)

        avg_views = total_views / total_videos if total_videos > 0 else 0

        stats_text = (
            f"Total Videos: {total_videos} | "
            f"Total Views: {total_views:,} | "
            f"Average Views: {avg_views:,.1f} | "
            f"Total Engagements: {total_comments + total_likes + total_shares:,}"
        )

        self.stats_label.configure(text=stats_text)

        # Log
        self._log(f"Fetched {total_videos} videos with {total_views:,} total views")

        # Switch to data tab
        self.notebook.select(self.data_tab)

    def _show_video_details(self, event):
        """Show detailed information about a selected video"""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        # Get the video data
        idx = int(selected_item[0])
        video = self.video_data[idx]

        # Create detail window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Video Details")
        detail_window.geometry("600x500")
        detail_window.minsize(500, 400)

        # Make it modal
        detail_window.transient(self.root)
        detail_window.grab_set()

        # Create detail view
        detail_frame = ttk.Frame(detail_window, padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            detail_frame, text=video.get("title", "Untitled"), font=("", 14, "bold"), wraplength=550
        )
        title_label.pack(fill=tk.X, pady=5)

        # Create a notebook for details
        detail_notebook = ttk.Notebook(detail_frame)
        detail_notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Basic info tab
        basic_tab = ttk.Frame(detail_notebook, padding=10)
        detail_notebook.add(basic_tab, text="Basic Info")

        # Format timestamps
        created_time = video.get("created_time", "")
        if created_time:
            try:
                created_time = pd.to_datetime(created_time).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        updated_time = video.get("updated_time", "")
        if updated_time:
            try:
                updated_time = pd.to_datetime(updated_time).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        # Basic info fields
        info_text = (
            f"Video ID: {video.get('id', 'N/A')}\n\n"
            f"Created: {created_time}\n"
            f"Updated: {updated_time}\n\n"
            f"Duration: {video.get('length', 0)} seconds\n\n"
            f"Views: {video.get('views', 0):,}\n"
            f"Comments: {video.get('comments_count', 0):,}\n"
            f"Likes: {video.get('likes_count', 0):,}\n"
            f"Shares: {video.get('shares_count', 0):,}\n\n"
            f"URL: {video.get('permalink_url', 'N/A')}"
        )

        # Display basic info
        info_display = scrolledtext.ScrolledText(basic_tab, wrap=tk.WORD, height=15)
        info_display.pack(fill=tk.BOTH, expand=True)
        info_display.insert(tk.END, info_text)
        info_display.config(state=tk.DISABLED)

        # URL button
        url = video.get("permalink_url")
        if url:

            def open_url():
                import webbrowser

                webbrowser.open(url)

            ttk.Button(basic_tab, text="Open in Browser", command=open_url).pack(pady=5)

        # Description tab
        desc_tab = ttk.Frame(detail_notebook, padding=10)
        detail_notebook.add(desc_tab, text="Description")

        desc_text = video.get("description", "No description available.")

        desc_display = scrolledtext.ScrolledText(desc_tab, wrap=tk.WORD, height=15)
        desc_display.pack(fill=tk.BOTH, expand=True)
        desc_display.insert(tk.END, desc_text)
        desc_display.config(state=tk.DISABLED)

        # Insights tab if available
        insights_keys = [key for key in video.keys() if key.startswith("total_")]
        if insights_keys:
            insights_tab = ttk.Frame(detail_notebook, padding=10)
            detail_notebook.add(insights_tab, text="Insights")

            insights_text = "Video Insights:\n\n"
            for key in sorted(insights_keys):
                # Format key for display
                display_key = key.replace("total_", "").replace("_", " ").title()
                insights_text += f"{display_key}: {video.get(key, 0):,}\n"

            insights_display = scrolledtext.ScrolledText(insights_tab, wrap=tk.WORD, height=15)
            insights_display.pack(fill=tk.BOTH, expand=True)
            insights_display.insert(tk.END, insights_text)
            insights_display.config(state=tk.DISABLED)

        # JSON tab for all data
        json_tab = ttk.Frame(detail_notebook, padding=10)
        detail_notebook.add(json_tab, text="Raw Data")

        json_text = json.dumps(video, indent=2)

        json_display = scrolledtext.ScrolledText(json_tab, wrap=tk.WORD, height=15, font=("Courier", 10))
        json_display.pack(fill=tk.BOTH, expand=True)
        json_display.insert(tk.END, json_text)
        json_display.config(state=tk.DISABLED)

        # Close button
        ttk.Button(detail_frame, text="Close", command=detail_window.destroy).pack(pady=10)

        # Center the window
        detail_window.update_idletasks()
        width = detail_window.winfo_width()
        height = detail_window.winfo_height()
        x = (detail_window.winfo_screenwidth() // 2) - (width // 2)
        y = (detail_window.winfo_screenheight() // 2) - (height // 2)
        detail_window.geometry(f"{width}x{height}+{x}+{y}")

    def _export_data(self):
        """Export data using the selected format"""
        if not self.video_data:
            messagebox.showerror("Error", "No data to export")
            return

        export_format = self.export_format_var.get()

        if export_format == "CSV":
            self._export_to_csv()
        else:  # Google Sheets
            self._export_to_google_sheet()

    def _export_to_csv(self):
        """Export data to CSV file"""
        output_dir = self.output_path_var.get()

        if not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Invalid output directory")
            return

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"facebook_video_data_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)

        self.status_var.set("Exporting to CSV...")
        self._log(f"Exporting data to CSV: {filepath}")

        try:
            # Initialize API
            access_token = self._get_access_token()
            if not access_token:
                return

            self.fb_api = fbvdata.FacebookAPI(access_token)

            # Export
            result = self.fb_api.export_to_csv(self.video_data, filepath)

            self._log(f"Export successful: {result}")
            self.status_var.set("Export complete")

            # Ask to open the file or directory
            if messagebox.askyesno("Export Complete", f"Data exported to:\n{filepath}\n\nOpen containing folder?"):
                self._open_file_location(filepath)

        except Exception as e:
            self._log(f"Error exporting to CSV: {e}")
            messagebox.showerror("Export Error", f"Failed to export to CSV: {e}")
            self.status_var.set("Export failed")

    def _export_to_google_sheet(self):
        """Export data to Google Sheets"""
        spreadsheet_name = self.spreadsheet_name_var.get()
        worksheet_name = self.worksheet_name_var.get()

        # Check for credentials
        credentials_path = self.credentials_path_var.get()
        if not credentials_path or not os.path.isfile(credentials_path):
            messagebox.showerror("Error", "Google API credentials file not found")
            return

        # Set environment variable
        os.environ["GOOGLE_CREDENTIALS_PATH"] = credentials_path

        self.status_var.set("Exporting to Google Sheets...")
        self._log(f"Exporting data to Google Sheets: {spreadsheet_name}/{worksheet_name}")

        # Run in a thread to avoid freezing UI
        threading.Thread(target=self._export_to_google_thread, args=(spreadsheet_name, worksheet_name)).start()

    def _export_to_google_thread(self, spreadsheet_name, worksheet_name):
        """Thread for Google Sheets export"""
        try:
            # Initialize API
            access_token = self._get_access_token()
            if not access_token:
                return

            self.fb_api = fbvdata.FacebookAPI(access_token)

            # Export
            sheet_url = self.fb_api.export_to_google_sheet(
                self.video_data, spreadsheet_name=spreadsheet_name, worksheet_name=worksheet_name
            )

            self._log(f"Export successful: {sheet_url}")

            # Show success message with link
            self.root.after(0, lambda: self._show_google_export_success(sheet_url))

        except Exception as e:
            self._log(f"Error exporting to Google Sheets: {e}")
            error_message = str(e)  # Capture the error message
            self.root.after(
                0, lambda: messagebox.showerror("Export Error", f"Failed to export to Google Sheets: {error_message}")
            )
            self.root.after(0, lambda: self.status_var.set("Export failed"))

    def _show_google_export_success(self, sheet_url):
        """Show success message with Google Sheet link"""
        self.status_var.set("Export complete")

        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Successful")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Message
        ttk.Label(dialog, text="Data successfully exported to Google Sheets!", font=("", 12, "bold")).pack(
            pady=(20, 10)
        )

        # URL display
        url_frame = ttk.Frame(dialog)
        url_frame.pack(fill=tk.X, padx=20, pady=10)

        url_entry = ttk.Entry(url_frame, width=50)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        url_entry.insert(0, sheet_url)
        url_entry.config(state="readonly")

        # Copy button
        def copy_url():
            dialog.clipboard_clear()
            dialog.clipboard_append(sheet_url)
            copy_btn.config(text="Copied!")
            dialog.after(1000, lambda: copy_btn.config(text="Copy"))

        copy_btn = ttk.Button(url_frame, text="Copy", command=copy_url)
        copy_btn.pack(side=tk.LEFT, padx=5)

        # Open button
        def open_url():
            import webbrowser

            webbrowser.open(sheet_url)

        ttk.Button(dialog, text="Open in Browser", command=open_url).pack(pady=5)

        # Close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _clear_data(self):
        """Clear all loaded data"""
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear data list
        self.video_data = []

        # Update stats
        self.stats_label.configure(text="No data loaded")

        self._log("Data cleared")

    def _get_access_token(self):
        """Get access token from UI or file"""
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
                self._log(f"Error loading token from file: {e}")
                return None
        else:
            token = self.access_token_var.get().strip()
            if not token:
                messagebox.showerror("Error", "Please enter an Access Token")
                return None
            return token

    def _log(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        # Enable editing
        self.log_text.config(state=tk.NORMAL)

        # Add message
        self.log_text.insert(tk.END, log_message)

        # Auto-scroll to end
        self.log_text.see(tk.END)

        # Disable editing
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        """Clear the log text"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._log("Log cleared")

    def _save_log(self):
        """Save the log to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"fbv_log_{timestamp}.txt"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=default_filename,
        )

        if not file_path:
            return

        try:
            log_content = self.log_text.get(1.0, tk.END)
            with open(file_path, "w") as f:
                f.write(log_content)

            self._log(f"Log saved to: {file_path}")

            # Ask to open the file
            if messagebox.askyesno("Log Saved", f"Log saved to:\n{file_path}\n\nOpen file?"):
                self._open_file(file_path)

        except (IOError, OSError) as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")

    def _open_file(self, filepath):
        """Open a file with the default application"""
        try:
            import os
            import platform
            import subprocess

            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(("open", filepath))
            else:  # Linux and other Unix-like
                subprocess.call(("xdg-open", filepath))
        except (OSError, subprocess.SubprocessError) as e:
            self._log(f"Error opening file: {e}")

    def _open_file_location(self, filepath):
        """Open the folder containing a file"""
        try:
            import os
            import platform
            import subprocess

            directory = os.path.dirname(os.path.abspath(filepath))

            if platform.system() == "Windows":
                subprocess.call(f'explorer "{directory}"', shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", directory])
            else:  # Linux and other Unix-like
                subprocess.call(["xdg-open", directory])
        except (OSError, subprocess.SubprocessError) as e:
            self._log(f"Error opening directory: {e}")

    def _load_settings(self):
        """Load saved settings from file"""
        settings_path = os.path.join(os.path.expanduser("~"), ".fbvdata_settings.json")

        if os.path.isfile(settings_path):
            try:
                with open(settings_path, "r") as f:
                    settings = json.load(f)

                # Apply settings
                if "page_id" in settings:
                    self.page_id_var.set(settings["page_id"])

                if "token_from_file" in settings:
                    self.token_from_file_var.set(settings["token_from_file"])
                    self._toggle_token_source()

                if "token_path" in settings:
                    self.token_path_var.set(settings["token_path"])

                if "max_videos" in settings:
                    self.max_videos_var.set(settings["max_videos"])

                if "export_format" in settings:
                    self.export_format_var.set(settings["export_format"])
                    self._toggle_export_options()

                if "spreadsheet_name" in settings:
                    self.spreadsheet_name_var.set(settings["spreadsheet_name"])

                if "worksheet_name" in settings:
                    self.worksheet_name_var.set(settings["worksheet_name"])

                if "output_path" in settings and os.path.isdir(settings["output_path"]):
                    self.output_path_var.set(settings["output_path"])

                if "credentials_path" in settings and os.path.isfile(settings["credentials_path"]):
                    self.credentials_path_var.set(settings["credentials_path"])
                    os.environ["GOOGLE_CREDENTIALS_PATH"] = settings["credentials_path"]

                self._log("Settings loaded")

            except (IOError, json.JSONDecodeError) as e:
                self._log(f"Error loading settings: {e}")

    def _save_settings(self, event=None):
        """Save settings to file"""
        settings = {
            "page_id": self.page_id_var.get(),
            "token_from_file": self.token_from_file_var.get(),
            "token_path": self.token_path_var.get(),
            "max_videos": self.max_videos_var.get(),
            "export_format": self.export_format_var.get(),
            "spreadsheet_name": self.spreadsheet_name_var.get(),
            "worksheet_name": self.worksheet_name_var.get(),
            "output_path": self.output_path_var.get(),
            "credentials_path": self.credentials_path_var.get(),
        }

        settings_path = os.path.join(os.path.expanduser("~"), ".fbvdata_settings.json")

        try:
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)

            # No log message to avoid spam during normal use
        except (IOError, OSError) as e:
            self._log(f"Error saving settings: {e}")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    root.mainloop()


if __name__ == "__main__":
    main()
