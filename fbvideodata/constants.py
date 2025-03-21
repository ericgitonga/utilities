"""
Constants for the Facebook Video Data Tool application.
"""

# Application info
APP_NAME = "Facebook Video Data Tool"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Tool for retrieving and analyzing Facebook video data"
APP_ICON = "fbv_icon.ico"

# Default settings
DEFAULT_MAX_VIDEOS = 25
DEFAULT_EXPORT_FORMAT = "CSV"
DEFAULT_SPREADSHEET_NAME = "Facebook Video Data"
DEFAULT_WORKSHEET_NAME = "Video Data"
DEFAULT_OUTPUT_PATH = "~/Documents"

# Settings file
SETTINGS_FILENAME = ".fbvdata_settings.json"

# Facebook API settings
FB_API_VERSION = "v18.0"  # Configurable API version
FB_API_BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}/"
FB_REQUIRED_PERMISSIONS = ["pages_read_engagement", "pages_show_list", "pages_read_user_content"]

# Help text
PAGE_ID_HELP_TEXT = """
To find your Facebook Page ID:

1. Go to your Facebook Page
2. Look at the URL. If it's in the format:
   https://www.facebook.com/YourPageName/
   Then 'YourPageName' is your Page ID

3. If you need the numeric ID, use Facebook's Graph API Explorer
   and query for 'me' with a Page token to see your page's numeric ID.
"""

TOKEN_HELP_TEXT = """
To get a Facebook API Access Token:

1. Go to developers.facebook.com and log in
2. Create a new App if you don't have one
3. Go to Tools & Support > Graph API Explorer
4. Select your App from the dropdown
5. Click 'Generate Access Token'
6. Make sure to select the following permissions:
   - pages_read_engagement
   - pages_show_list
   - pages_read_user_content
7. Click 'Generate Access Token' and copy the token

Note: For a longer-lived token, use the Access Token Debugger tool.
"""

GOOGLE_CREDENTIALS_HELP_TEXT = """
To set up Google Sheets integration:

1. Go to https://console.cloud.google.com/
2. Create a new project
3. Go to 'APIs & Services' > 'Library'
4. Enable 'Google Sheets API' and 'Google Drive API'
5. Go to 'APIs & Services' > 'Credentials'
6. Click 'Create Credentials' > 'Service account'
7. Fill in service account details and grant 'Editor' role
8. Create a JSON key and download it
9. Select this JSON file in the Credentials File field
10. If using an existing sheet, share it with the service account email address
"""
