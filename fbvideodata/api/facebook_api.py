"""
Facebook API module for retrieving video data.
"""

import requests
import pandas as pd

from ..utils import get_logger
from ..constants import FB_API_BASE_URL


class FacebookAPI:
    """Facebook Graph API wrapper for video data retrieval."""

    def __init__(self, access_token):
        """
        Initialize the Facebook API wrapper.

        Args:
            access_token: Facebook API access token
        """
        self.access_token = access_token
        self.api_base_url = FB_API_BASE_URL
        self.logger = get_logger()

    def _make_request(self, endpoint, params=None):
        """
        Make a request to the Facebook Graph API.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            dict: API response data

        Raises:
            requests.RequestException: If the request fails
            ValueError: If the API returns an error
        """
        if params is None:
            params = {}

        # Add access token to params
        params["access_token"] = self.access_token

        # Make request
        url = f"{self.api_base_url}{endpoint}"
        response = requests.get(url, params=params)

        # Check for errors
        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            error_code = error_data.get("error", {}).get("code", "Unknown code")
            error_type = error_data.get("error", {}).get("type", "Unknown type")

            self.logger.log(f"API Error: {error_code} {error_type} - {error_message}")
            raise ValueError(f"API Error ({error_code}): {error_message}")

        return response.json()

    def get_page_videos(self, page_id, limit=25, after=None):
        """
        Get videos for a Facebook page.

        Args:
            page_id: Facebook page ID
            limit: Maximum number of videos to fetch
            after: Pagination cursor

        Returns:
            dict: API response with video data
        """
        # Define fields to fetch
        fields = [
            "id",
            "title",
            "description",
            "created_time",
            "updated_time",
            "permalink_url",
            "length",
            "views",
            "comments.limit(0).summary(true)",
            "likes.limit(0).summary(true)",
            "shares",
            "saved.limit(0).summary(true)",
            "reach",
            "video_insights{total_video_views,total_video_impressions,total_video_view_time,total_video_views_by_follower_status,total_video_views_by_distribution_type,total_video_view_time_by_age_bucket_and_gender,total_video_view_time_by_region_id,total_video_view_time_by_distribution_type}",
        ]

        # Build params
        params = {"fields": ",".join(fields), "limit": limit}

        # Add pagination if present
        if after:
            params["after"] = after

        # Make request
        endpoint = f"{page_id}/videos"
        return self._make_request(endpoint, params)

    def get_video_insights(self, video_id):
        """
        Get insights data for a specific video.

        Args:
            video_id: Facebook video ID

        Returns:
            dict: API response with insights data
        """
        # Define insights metrics
        metrics = [
            "total_video_views",
            "total_video_impressions",
            "total_video_view_time",
            "total_video_complete_views",
            "total_video_30s_views",
            "total_video_views_by_follower_status",
        ]

        # Get insights
        endpoint = f"{video_id}/video_insights"
        params = {"metric": ",".join(metrics)}

        return self._make_request(endpoint, params)

    def export_to_csv(self, video_data, filepath):
        """
        Export video data to CSV file.

        Args:
            video_data: List of video data dictionaries
            filepath: Path to save the CSV file

        Returns:
            str: Path to the saved file
        """
        # Process the data
        processed_data = []

        for video in video_data:
            # Extract basic data
            video_processed = {
                "id": video.get("id", ""),
                "title": video.get("title", ""),
                "description": video.get("description", ""),
                "created_time": video.get("created_time", ""),
                "updated_time": video.get("updated_time", ""),
                "length_seconds": video.get("length", 0),
                "views": video.get("views", 0),
                "reach": video.get("reach", 0),
                "comments_count": video.get("comments_count", 0),
                "likes_count": video.get("likes_count", 0),
                "shares_count": video.get("shares_count", 0),
                "saves_count": video.get("saves_count", 0),
                "permalink_url": video.get("permalink_url", ""),
                "avg_watch_time": video.get("avg_watch_time", 0),
                "total_watch_time": video.get("total_watch_time", 0),
                "views_from_followers": video.get("views_from_followers", 0),
                "views_from_non_followers": video.get("views_from_non_followers", 0),
                "follower_percentage": video.get("follower_percentage", 0),
            }

            # Add any insight metrics
            for key in video:
                if key.startswith("total_"):
                    video_processed[key] = video[key]

            processed_data.append(video_processed)

        # Create DataFrame and export
        df = pd.DataFrame(processed_data)
        df.to_csv(filepath, index=False)

        return filepath


def get_all_facebook_video_data(page_id, access_token, max_videos=25):
    """
    Retrieve all video data for a Facebook page.

    Args:
        page_id: Facebook page ID
        access_token: Facebook API access token
        max_videos: Maximum number of videos to fetch

    Returns:
        list: List of video data dictionaries
    """
    logger = get_logger()
    logger.log(f"Retrieving video data for page: {page_id}")

    # Initialize API
    fb_api = FacebookAPI(access_token)

    # Get videos with pagination
    videos = []
    after = None
    total_fetched = 0

    while total_fetched < max_videos:
        # Determine how many to fetch in this batch
        remaining = max_videos - total_fetched
        batch_limit = min(25, remaining)  # API limit is 25 per request

        # Fetch batch
        result = fb_api.get_page_videos(page_id, limit=batch_limit, after=after)

        if not result or "data" not in result or not result["data"]:
            break

        # Process videos in this batch
        batch_videos = result["data"]
        logger.log(f"Fetched {len(batch_videos)} videos (batch)")

        # For each video, get additional data
        for video in batch_videos:
            # Extract engagement counts from API response
            try:
                video["comments_count"] = video.get("comments", {}).get("summary", {}).get("total_count", 0)
                video["likes_count"] = video.get("likes", {}).get("summary", {}).get("total_count", 0)
                video["shares_count"] = video.get("shares", {}).get("count", 0)
                video["saves_count"] = video.get("saved", {}).get("summary", {}).get("total_count", 0)

                # Process video insights data
                if "video_insights" in video and "data" in video["video_insights"]:
                    insights_data = video["video_insights"]["data"]

                    for insight in insights_data:
                        name = insight.get("name")
                        values = insight.get("values", [])

                        if not values:
                            continue

                        value = values[0].get("value")

                        if name == "total_video_view_time":
                            # Convert to seconds
                            video["total_watch_time"] = value / 1000 if isinstance(value, (int, float)) else 0
                            if video["views"] > 0:
                                video["avg_watch_time"] = video["total_watch_time"] / video["views"]
                            else:
                                video["avg_watch_time"] = 0

                        elif name == "total_video_views_by_follower_status" and isinstance(value, dict):
                            video["views_from_followers"] = value.get("follower", 0)
                            video["views_from_non_followers"] = value.get("non_follower", 0)

                        # Store the raw insight value too
                        video[name] = value

            except (KeyError, AttributeError) as e:
                logger.log(f"Error extracting metrics for video {video.get('id')}: {e}")
                video["comments_count"] = 0
                video["likes_count"] = 0
                video["shares_count"] = 0
                video["saves_count"] = 0

            # Add to the list
            videos.append(video)

        # Update counts
        total_fetched += len(batch_videos)
        logger.log(f"Fetched {total_fetched}/{max_videos} videos (total)")

        # Check for more pages
        if "paging" in result and "cursors" in result["paging"] and "after" in result["paging"]["cursors"]:
            after = result["paging"]["cursors"]["after"]
        else:
            break

    logger.log(f"Completed retrieving {len(videos)} videos")
    return videos
