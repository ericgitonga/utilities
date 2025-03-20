# Facebook Video Data Tool

A GUI application for non-programmers to easily retrieve, analyze, and export Facebook video data.

## Features

- **Simple Interface**: Easy-to-use GUI requiring no programming knowledge
- **Data Retrieval**: Fetch video metrics from any Facebook page
- **Data Visualization**: View and sort video data in a clean tabular format
- **Detailed Video Analysis**: See in-depth metrics for each video
- **Export Options**: Save data to CSV or Google Sheets
- **Persistent Settings**: Your configuration is saved between sessions

## Requirements

- A Facebook Developer Account
- Facebook Graph API Access Token
- Google API credentials (optional, for Google Sheets export)

## Installation

### Windows

1. Download the installer from the releases page
2. Run the installer and follow the prompts
3. The application will be installed and a desktop shortcut will be created

### Manual Installation

If you prefer to run from source:

1. Ensure you have Python 3.7+ installed
2. Clone this repository or download the source code
3. Install required packages: `pip install -r requirements.txt`
4. Run the application: `python fb_video_gui.py`

## Getting Started

### Setup Tab

1. Enter your Facebook Page ID
2. Enter your Facebook API Access Token
   - You can also load the token from a file for security
3. Set the maximum number of videos to retrieve
4. For Google Sheets export, select your Google API credentials file
5. Test your connection to ensure everything is working

### Using the Application

1. Click "Fetch Video Data" to retrieve videos from the specified page
2. View the video data in the Data tab
3. Double-click any video to see detailed information
4. Export your data using the Export tab
5. View the application log in the Log tab

## Obtaining Access Tokens

### Facebook Access Token

1. Go to [Facebook for Developers](https://developers.facebook.com/)
2. Create a developer account if you don't have one
3. Create a new app or use an existing one
4. Go to Tools & Support > Graph API Explorer
5. Select your app from the dropdown
6. Click "Generate Access Token"
7. Select the following permissions:
   - pages_read_engagement
   - pages_show_list
   - pages_read_user_content
8. Click "Generate Access Token" and copy the token

For a longer-lasting token, use the Access Token Debugger tool to convert to a long-lived token.

### Google API Credentials

For Google Sheets export:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Sheets API and Google Drive API
4. Create a service account with Editor permissions
5. Download the JSON credentials file
6. Share your Google Sheet with the service account email address

## Troubleshooting

- **Connection Issues**: Ensure your access token hasn't expired
- **No Videos Found**: Verify you have the correct Page ID
- **Google Sheets Export Fails**: Check that your credentials file is valid and the service account has permission to access the sheet

## Privacy & Security

- Your access tokens and credentials are stored locally on your computer
- No data is sent to any servers other than Facebook and Google APIs
- The application does not track usage or collect any analytics

## License

This software is released under the MIT License. See LICENSE file for details.
