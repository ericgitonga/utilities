"""
Google Sheets API integration for exporting data.
"""

import os
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe

from ..utils import get_logger


class GoogleSheetsAPI:
    """Google Sheets API wrapper for exporting data."""

    def __init__(self, credentials_path=None):
        """
        Initialize the Google Sheets API wrapper.

        Args:
            credentials_path: Path to Google API credentials JSON file
        """
        self.logger = get_logger()

        # Get credentials path from environment if not provided
        if credentials_path is None:
            credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")

        if not credentials_path or not os.path.isfile(credentials_path):
            raise ValueError("Google API credentials file not found")

        self.credentials_path = credentials_path

        # Define scope
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # Authenticate
        self._authenticate()

    def _authenticate(self):
        """
        Authenticate with Google API.

        Raises:
            ValueError: If authentication fails
        """
        try:
            # Authenticate
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, self.scope)
            self.client = gspread.authorize(credentials)
            self.logger.log("Authenticated with Google Sheets API")
        except Exception as e:
            self.logger.log(f"Google Sheets authentication error: {e}")
            raise ValueError(f"Failed to authenticate with Google Sheets API: {e}")

    def export_dataframe(self, df, spreadsheet_name, worksheet_name="Sheet1", create_if_missing=True):
        """
        Export a DataFrame to Google Sheets.

        Args:
            df: Pandas DataFrame to export
            spreadsheet_name: Name of the Google Spreadsheet
            worksheet_name: Name of the worksheet
            create_if_missing: Create spreadsheet/worksheet if not found

        Returns:
            str: URL of the spreadsheet

        Raises:
            ValueError: If spreadsheet operations fail
        """
        # Find or create spreadsheet
        try:
            # Try to open existing spreadsheet
            spreadsheet = self.client.open(spreadsheet_name)
            self.logger.log(f"Found existing spreadsheet: {spreadsheet_name}")
        except gspread.SpreadsheetNotFound:
            if create_if_missing:
                # Create new spreadsheet
                spreadsheet = self.client.create(spreadsheet_name)
                self.logger.log(f"Created new spreadsheet: {spreadsheet_name}")
            else:
                self.logger.log(f"Spreadsheet not found: {spreadsheet_name}")
                raise ValueError(f"Spreadsheet '{spreadsheet_name}' not found")

        # Find or create worksheet
        try:
            # Try to get existing worksheet
            worksheet = spreadsheet.worksheet(worksheet_name)
            self.logger.log(f"Using existing worksheet: {worksheet_name}")

            # Clear existing content
            worksheet.clear()
        except gspread.WorksheetNotFound:
            if create_if_missing:
                # Create new worksheet
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=df.shape[0] + 10, cols=df.shape[1] + 5)
                self.logger.log(f"Created new worksheet: {worksheet_name}")
            else:
                self.logger.log(f"Worksheet not found: {worksheet_name}")
                raise ValueError(f"Worksheet '{worksheet_name}' not found")

        # Update worksheet with DataFrame
        try:
            set_with_dataframe(worksheet, df)
            self.logger.log(f"Exported {df.shape[0]} rows to Google Sheets")

            # Format the worksheet
            worksheet.format("1:1", {"textFormat": {"bold": True}})

            # Resize columns to fit content
            for i, column in enumerate(df.columns, start=1):
                max_length = max(len(str(column)), df[column].astype(str).map(len).max() if df.shape[0] > 0 else 0)
                worksheet.set_column_width(i, min(max_length * 9, 250))

            # Return the spreadsheet URL
            return spreadsheet.url
        except Exception as e:
            self.logger.log(f"Error exporting to Google Sheets: {e}")
            raise ValueError(f"Failed to export to Google Sheets: {e}")


def export_to_google_sheet(
    video_data, credentials_path=None, spreadsheet_name="Facebook Video Data", worksheet_name="Video Data"
):
    """
    Export video data to Google Sheets.

    Args:
        video_data: List of video data dictionaries
        credentials_path: Path to Google API credentials JSON file
        spreadsheet_name: Name of the Google Spreadsheet
        worksheet_name: Name of the worksheet

    Returns:
        str: URL of the spreadsheet
    """
    logger = get_logger()

    # Check for credentials
    if credentials_path is None:
        credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")

    if not credentials_path or not os.path.isfile(credentials_path):
        raise ValueError("Google API credentials file not found")

    # Process data for export
    processed_data = []
    for video in video_data:
        # Extract basic data
        video_processed = {
            "Video ID": video.get("id", ""),
            "Title": video.get("title", ""),
            "Created": video.get("created_time", ""),
            "Updated": video.get("updated_time", ""),
            "Length (sec)": video.get("length", 0),
            "Views": video.get("views", 0),
            "Comments": video.get("comments_count", 0),
            "Likes": video.get("likes_count", 0),
            "Shares": video.get("shares_count", 0),
            "URL": video.get("permalink_url", ""),
        }

        # Add any insight metrics
        for key in video:
            if key.startswith("total_"):
                # Format the key for display
                display_key = key.replace("total_", "").replace("_", " ").title()
                video_processed[display_key] = video[key]

        processed_data.append(video_processed)

    # Create DataFrame
    df = pd.DataFrame(processed_data)

    # Initialize Google Sheets API
    gs_api = GoogleSheetsAPI(credentials_path)

    # Export data
    logger.log(f"Exporting {len(processed_data)} videos to Google Sheets")
    sheet_url = gs_api.export_dataframe(df, spreadsheet_name, worksheet_name)

    return sheet_url
