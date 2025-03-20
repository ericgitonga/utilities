# Facebook Video Data Tool

A GUI application for non-programmers to easily retrieve, analyze, and export Facebook video data.

Copyright © 2025 Eric Gitonga. All rights reserved.

## Features

- **Simple Interface**: Easy-to-use GUI requiring no programming knowledge
- **Data Retrieval**: Fetch video metrics from any Facebook page
- **Data Visualization**: View and sort video data in a clean tabular format
- **Detailed Video Analysis**: See in-depth metrics for each video
- **Export Options**: Save data to CSV or Google Sheets
- **Persistent Settings**: Your configuration is saved between sessions

## Installation Guide

### Windows Installation

#### Method 1: Using the Windows Installer (Recommended)

1. Download the installer (`FBVideoDataTool_Setup.exe`) from the [Releases page](https://github.com/ericgitonga/utilities/releases)
2. Double-click the installer to start the installation process
3. Follow the on-screen instructions
4. Once installation is complete, you'll find the Facebook Video Data Tool in your Start Menu and on your Desktop

#### Method 2: Using the Python Installer Script

If the Windows installer isn't available, you can use the Python installer script:

1. Make sure you have Python 3.7 or newer installed
   - If not, download and install it from [python.org](https://www.python.org/downloads/)
   - During installation, check the option "Add Python to PATH"
2. Download `install.py` from the [Releases page](https://github.com/ericgitonga/utilities/releases)
3. Right-click on `install.py` and select "Open with Python"
4. The installer will automatically:
   - Install all necessary dependencies
   - Download the application
   - Create a desktop shortcut
5. Follow any on-screen instructions from the installer

### Linux Installation

#### Method 1: Using the Debian Package (Ubuntu, Debian, Mint, etc.)

1. Download the `.deb` package from the [Releases page](https://github.com/ericgitonga/utilities/releases)
2. Install it using one of these methods:
   - Double-click the `.deb` file and follow the prompts in your package manager
   - Or open a terminal and run: `sudo dpkg -i facebook-video-data-tool_1.0.0_all.deb`
   - If you get dependency errors, run: `sudo apt-get install -f`
3. Once installed, you can find the application in your Applications menu

#### Method 2: Using the Python Installer Script

For Linux distributions that don't use `.deb` packages:

1. Make sure you have Python 3.7 or newer installed
   - If not, install it using your distribution's package manager
   - For example, on Fedora: `sudo dnf install python3`
2. Open a terminal and run:
   ```
   wget https://github.com/ericgitonga/utilities/releases/download/v1.0.0/install.py
   chmod +x install.py
   ./install.py
   ```
3. The installer will automatically:
   - Install all necessary dependencies
   - Download the application
   - Create a desktop shortcut
4. Follow any on-screen instructions from the installer

### Manual Installation (Advanced Users Only)

If all else fails, you can install the application manually:

1. Make sure Python 3.7 or newer and pip are installed
2. Download the source code from the [Releases page](https://github.com/ericgitonga/utilities/releases)
3. Extract the zip file
4. Open a terminal/command prompt in the extracted directory
5. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
6. Run the application:
   ```
   python -m fbvideodata.main
   ```

## User Guide

### Getting Started

Before using the Facebook Video Data Tool, you need to set up access to Facebook's API:

1. Go to the Facebook Developer Portal at [developers.facebook.com](https://developers.facebook.com/)
2. Create a developer account if you don't have one
3. Create a new app or use an existing one
4. Navigate to the Graph API Explorer tool
5. Generate an access token with the following permissions:
   - pages_read_engagement
   - pages_show_list
   - pages_read_user_content
6. Copy the token for use in the application

### Setup Tab

The Setup tab is where you configure your Facebook API connection:

1. **Facebook Page ID**: Enter the ID of the Facebook page you want to analyze
   - This can be the name in the URL (e.g., "cocacola") or the numeric ID
   - Click the "?" button for help finding your Page ID
   
2. **Access Token**: Enter the Facebook API access token you generated
   - You can toggle visibility with the "Show" button
   - For security, you can store the token in a file and load it using the "Load token from file" option
   
3. **Maximum Videos**: Set how many videos to retrieve (up to 1000)

4. **Google Sheets Configuration** (Optional): 
   - If you want to export to Google Sheets, select your Google API credentials file
   - Click "Setup Google Credentials Help" for instructions on creating this file

5. **Test Connection**: Click this button to verify your Facebook API access before retrieving data

### Data Tab

The Data tab displays video data and provides analysis:

1. **Fetch Video Data**: Click this button to retrieve videos from the Facebook page
   - Data is displayed in a table with columns for title, date, views, reach, comments, likes, shares, and watch time
   - You can sort by any column by clicking the column header
   
2. **Clear Data**: Removes all currently loaded data

3. **Statistics**: Shows a summary of your video data at the bottom
   - Total videos, total views, average views, average watch time, and total engagements
   
4. **Video Details**: Double-click any video to open a detailed view with:
   - **Basic Info**: Title, ID, dates, views, reach, likes, comments, shares, saves
   - **Watch Time**: Average watch time, total watch time, and audience breakdown (followers vs non-followers)
   - **Description**: Full video description
   - **Insights**: Additional metrics from Facebook
   - **Raw Data**: Complete data in JSON format for advanced users
   - Link to open the video in your web browser

### Export Tab

The Export tab allows you to save your data for external use:

1. **Export Format**: Choose between CSV file or Google Sheets
   
2. **CSV Options**:
   - Select an output directory for the CSV file
   
3. **Google Sheets Options**:
   - Enter a spreadsheet name (creates a new one or uses existing)
   - Enter a worksheet name within the spreadsheet
   - Note: This requires Google API credentials from the Setup tab
   
4. **Export Data**: Creates your export file
   - For CSV exports, you'll be asked if you want to open the containing folder
   - For Google Sheets, you'll see a dialog with a link to the sheet
   - All metrics (including watch time, reach, and audience breakdown) are automatically included in the exports

### Log Tab

The Log tab shows a record of all application activity:

1. **Log Entries**: Each action in the application is recorded with a timestamp
   
2. **Clear Log**: Removes all current log entries
   
3. **Save Log**: Saves the current log to a text file of your choice

### Menu Options

The application menu provides additional functionality:

1. **File Menu**:
   - Exit: Close the application
   
2. **Help Menu**:
   - Check for Updates: Manually check if a new version is available
   - About: Shows version and copyright information

## Available Metrics

The Facebook Video Data Tool retrieves and displays the following metrics:

### Basic Metrics
- **Views**: Total number of video views
- **Reach**: Number of unique users who saw your video
- **Comments**: Number of comments on the video
- **Likes**: Number of likes/reactions received
- **Shares**: Number of times the video was shared
- **Saves**: Number of times users saved the video

### Watch Time Metrics
- **Average Watch Time**: Average time users spent watching the video
- **Total Watch Time**: Cumulative watch time across all views

### Audience Metrics
- **Views from Followers**: Views by users who follow your page
- **Views from Non-Followers**: Views by users who don't follow your page
- **Follower Percentage**: Percentage of views from followers

### Additional Insights
- **Video impressions**: Number of times the video appeared in feeds
- **Complete views**: Number of views where 95%+ of the video was watched
- **Regional data**: View breakdown by geographical regions (where available)

## Tips for Best Results

1. **Use a Page Manager Token**: Access tokens generated as a page manager provide more data
2. **Limit Initial Requests**: Start with a small number of videos to test
3. **Save Tokens Securely**: Use the "Load token from file" option for better security
4. **Regular Updates**: Check for application updates regularly for new features
5. **Save Exports**: Export data regularly as Facebook's API may change over time

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Verify your access token hasn't expired (they typically last 60 days)
   - Check your internet connection
   - Ensure the Page ID is correct

2. **No Videos Found**:
   - Confirm the page has public videos
   - Verify you have the correct permissions in your access token
   - Check if the page has restrictions on content access

3. **Missing or Incomplete Metrics**:
   - Some metrics require specific page sizes or minimum activity
   - Verify you're using a Page token rather than a User token
   - Recently published videos may not have complete metrics yet

4. **Google Sheets Export Fails**:
   - Verify your Google API credentials are correct
   - Ensure the service account has permission to create/edit sheets
   - Check that you have an internet connection

5. **Application Crashes**:
   - Check the log tab for error details
   - Ensure all dependencies are installed
   - Verify you're using Python 3.7 or newer

### Getting Help

If you encounter issues not covered in this guide:

1. Check the log for error messages
2. Visit the [GitHub Issues page](https://github.com/ericgitonga/utilities/issues) to see if others have reported similar problems
3. Open a new issue with details about your operating system, Python version, and the steps to reproduce the problem

## Privacy & Security

- Your access tokens and credentials are stored locally on your computer
- No data is sent to any servers other than Facebook and Google APIs
- The application does not track usage or collect any analytics

## Updates & Maintenance

- The application automatically checks for updates on startup
- You can manually check for updates through the Help menu
- New versions will be announced on the GitHub Releases page

## License

This software is released under the MIT License. See LICENSE file for details.

## Copyright

Copyright © 2025 Eric Gitonga. All rights reserved.
