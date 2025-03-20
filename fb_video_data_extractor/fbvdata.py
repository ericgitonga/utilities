import requests
import os
import pandas as pd
import time


class FacebookAPI:
    """
    A class to interact with Facebook Graph API to fetch video post data
    """

    def __init__(self, access_token=None):
        """
        Initialize the FacebookAPI class

        Parameters:
        -----------
        access_token : str, optional
            The Facebook Graph API access token. If not provided, it will try to load from environment variable.
        """
        self.base_url = "https://graph.facebook.com/v18.0"  # Using a recent API version

        # Try to get token from environment variable if not provided
        if access_token is None:
            access_token = os.environ.get("FACEBOOK_ACCESS_TOKEN")
            if not access_token:
                raise ValueError("Facebook access token not provided and not found in environment variables")

        self.access_token = access_token

    def get_page_videos(self, page_id, limit=25, fields=None):
        """
        Get videos from a Facebook page

        Parameters:
        -----------
        page_id : str
            ID of the Facebook page
        limit : int, optional
            Number of videos to retrieve (default 25)
        fields : list, optional
            List of specific fields to retrieve for each video

        Returns:
        --------
        dict
            JSON response containing video data
        """
        if fields is None:
            fields = [
                "id",
                "title",
                "description",
                "created_time",
                "updated_time",
                "length",
                "views",
                "permalink_url",
                "comments.limit(0).summary(true)",
                "likes.limit(0).summary(true)",
                "shares",
            ]

        endpoint = f"{self.base_url}/{page_id}/videos"

        params = {"access_token": self.access_token, "limit": limit, "fields": ",".join(fields)}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving page videos: {e}")
            return None

    def get_video_details(self, video_id, fields=None):
        """
        Get detailed information about a specific video

        Parameters:
        -----------
        video_id : str
            ID of the Facebook video
        fields : list, optional
            List of specific fields to retrieve

        Returns:
        --------
        dict
            JSON response containing detailed video data
        """
        if fields is None:
            fields = [
                "id",
                "title",
                "description",
                "created_time",
                "length",
                "views",
                "comments.limit(0).summary(true)",
                "likes.limit(0).summary(true)",
                "shares",
                "permalink_url",
                "source",
                "thumbnails",
                "captions",
                "live_status",
            ]

        endpoint = f"{self.base_url}/{video_id}"

        params = {"access_token": self.access_token, "fields": ",".join(fields)}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving video details: {e}")
            return None

    def get_video_insights(self, video_id, metrics=None):
        """
        Get insights/analytics for a specific video

        Parameters:
        -----------
        video_id : str
            ID of the Facebook video
        metrics : list, optional
            List of specific metrics to retrieve

        Returns:
        --------
        dict
            JSON response containing video insights data
        """
        if metrics is None:
            metrics = [
                "total_video_views",
                "total_video_views_unique",
                "total_video_complete_views",
                "total_video_view_time",
                "total_video_impressions",
                "total_video_impressions_unique",
                "total_video_sound_on",
                "total_video_10s_views",
            ]

        endpoint = f"{self.base_url}/{video_id}/video_insights"

        params = {"access_token": self.access_token, "metric": ",".join(metrics)}

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving video insights: {e}")
            return None

    def get_video_comments(self, video_id, limit=100):
        """
        Get comments for a specific video

        Parameters:
        -----------
        video_id : str
            ID of the Facebook video
        limit : int, optional
            Number of comments to retrieve (default 100)

        Returns:
        --------
        dict
            JSON response containing video comments
        """
        endpoint = f"{self.base_url}/{video_id}/comments"

        params = {
            "access_token": self.access_token,
            "limit": limit,
            "fields": "id,message,created_time,like_count,comment_count,from",
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving video comments: {e}")
            return None

    def export_to_csv(self, data, file_name="facebook_video_data.csv"):
        """
        Export video data to CSV

        Parameters:
        -----------
        data : list
            List of dictionaries containing video data
        file_name : str, optional
            Name of the output CSV file

        Returns:
        --------
        str
            Path to the saved CSV file
        """
        df = pd.DataFrame(data)

        # Format datetime columns
        for col in df.columns:
            if "time" in col and df[col].dtype == "object":
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception as e:
                    print(f"Error formatting time: {str(e)}")
                    pass

        # Save to CSV
        df.to_csv(file_name, index=False)
        print(f"Data exported to {file_name}")
        return file_name


def get_all_facebook_video_data(page_id, access_token=None, max_videos=100):
    """
    Comprehensive function to get all relevant video data from a Facebook page

    Parameters:
    -----------
    page_id : str
        ID of the Facebook page
    access_token : str, optional
        Facebook Graph API access token
    max_videos : int, optional
        Maximum number of videos to retrieve (default 100)

    Returns:
    --------
    list
        List of dictionaries containing comprehensive video data
    """
    # Initialize API
    fb_api = FacebookAPI(access_token)

    # Get videos from page
    page_videos = fb_api.get_page_videos(page_id, limit=max_videos)

    if not page_videos or "data" not in page_videos:
        print("No videos found or error in API response")
        return []

    all_video_data = []

    # Process each video
    for video in page_videos["data"]:
        video_id = video.get("id")

        if not video_id:
            continue

        # Get additional video details
        # details = fb_api.get_video_details(video_id)

        # Get video insights
        insights = fb_api.get_video_insights(video_id)

        # Get comments summary
        if "comments" in video and "summary" in video["comments"]:
            comments_count = video["comments"]["summary"].get("total_count", 0)
        else:
            comments_count = 0

        # Get likes summary
        if "likes" in video and "summary" in video["likes"]:
            likes_count = video["likes"]["summary"].get("total_count", 0)
        else:
            likes_count = 0

        # Format insights data
        formatted_insights = {}
        if insights and "data" in insights:
            for insight in insights["data"]:
                metric_name = insight.get("name")
                metric_value = insight.get("values", [{}])[0].get("value", 0)
                formatted_insights[metric_name] = metric_value

        # Create comprehensive video data record
        video_data = {
            "id": video_id,
            "title": video.get("title", ""),
            "description": video.get("description", ""),
            "created_time": video.get("created_time"),
            "updated_time": video.get("updated_time"),
            "length": video.get("length", 0),
            "views": video.get("views", 0),
            "comments_count": comments_count,
            "likes_count": likes_count,
            "shares_count": video.get("shares", {}).get("count", 0) if "shares" in video else 0,
            "permalink_url": video.get("permalink_url", ""),
        }

        # Add insights data
        video_data.update(formatted_insights)

        all_video_data.append(video_data)

        # Respect rate limits
        time.sleep(1)

    return all_video_data


# Example usage
if __name__ == "__main__":
    # Replace with your values
    PAGE_ID = "YOUR_PAGE_ID"  # The ID of the Facebook page
    ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"  # Your Facebook Graph API access token

    # To get environment variable instead
    # import os
    # ACCESS_TOKEN = os.environ.get('FACEBOOK_ACCESS_TOKEN')

    try:
        # Get all video data
        video_data = get_all_facebook_video_data(PAGE_ID, ACCESS_TOKEN)

        # Initialize API client
        fb_api = FacebookAPI(ACCESS_TOKEN)

        # Export to CSV
        if video_data:
            fb_api.export_to_csv(video_data, "facebook_video_analysis.csv")

        # Example: Get comments for a specific video
        if video_data:
            first_video_id = video_data[0]["id"]
            comments = fb_api.get_video_comments(first_video_id)
            print(f"Retrieved {len(comments.get('data', []))} comments for video {first_video_id}")

    except Exception as e:
        print(f"Error running script: {e}")
