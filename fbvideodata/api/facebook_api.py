"""
Facebook API module for retrieving video data with improved error handling.
"""

import requests
import pandas as pd
import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from ..utils import get_logger
from ..constants import FB_API_BASE_URL


class FacebookAPIError(BaseModel):
    """Pydantic model for Facebook API error response."""

    message: str = Field(..., description="Error message")
    type: str = Field(default="OAuthException", description="Error type")
    code: int = Field(default=0, description="Error code")
    fbtrace_id: Optional[str] = Field(default=None, description="Facebook trace ID")


class FacebookErrorResponse(BaseModel):
    """Pydantic model for Facebook API error wrapper."""

    error: FacebookAPIError


class FacebookPagingCursors(BaseModel):
    """Pydantic model for Facebook API paging cursors."""

    before: Optional[str] = Field(default=None, description="Cursor for previous page")
    after: Optional[str] = Field(default=None, description="Cursor for next page")


class FacebookPaging(BaseModel):
    """Pydantic model for Facebook API paging information."""

    cursors: Optional[FacebookPagingCursors] = Field(default=None, description="Paging cursors")
    previous: Optional[str] = Field(default=None, description="URL for previous page")
    next: Optional[str] = Field(default=None, description="URL for next page")


class FacebookVideoInsightValue(BaseModel):
    """Pydantic model for a single video insight value."""

    value: Any = Field(..., description="Insight value, can be various types")


class FacebookVideoInsight(BaseModel):
    """Pydantic model for Facebook video insight."""

    name: str = Field(..., description="Insight name")
    period: str = Field(..., description="Insight period")
    values: List[FacebookVideoInsightValue] = Field(..., description="Insight values")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    id: str = Field(..., description="Insight ID")


class FacebookVideoInsightsResponse(BaseModel):
    """Pydantic model for Facebook video insights response."""

    data: List[FacebookVideoInsight] = Field(default_factory=list, description="List of insights")
    paging: Optional[FacebookPaging] = Field(default=None, description="Paging information")


class FacebookCountSummary(BaseModel):
    """Pydantic model for count summary (used in likes, comments, etc.)."""

    total_count: int = Field(..., description="Total count")
    can_like: Optional[bool] = Field(default=None, description="Can the current user like")
    has_liked: Optional[bool] = Field(default=None, description="Has the current user liked")


class FacebookShares(BaseModel):
    """Pydantic model for shares count."""

    count: int = Field(default=0, description="Number of shares")


class FacebookRawVideo(BaseModel):
    """Pydantic model for raw Facebook video data from API."""

    id: str = Field(..., description="Video ID")
    title: Optional[str] = Field(default="", description="Video title")
    description: Optional[str] = Field(default="", description="Video description")
    created_time: str = Field(..., description="Creation timestamp")
    updated_time: Optional[str] = Field(default=None, description="Last update timestamp")
    permalink_url: Optional[str] = Field(default="", description="Permanent URL")
    length: Optional[float] = Field(default=0, description="Video length in seconds")
    views: Optional[int] = Field(default=0, description="View count")
    comments: Optional[Dict[str, Any]] = Field(default=None, description="Comments data")
    likes: Optional[Dict[str, Any]] = Field(default=None, description="Likes data")
    shares: Optional[FacebookShares] = Field(default=None, description="Shares data")
    saved: Optional[Dict[str, Any]] = Field(default=None, description="Saved data")
    reach: Optional[int] = Field(default=0, description="Reach count")
    video_insights: Optional[Dict[str, Any]] = Field(default=None, description="Video insights data")

    class Config:
        extra = "allow"  # Allow extra fields


class FacebookVideosResponse(BaseModel):
    """Pydantic model for Facebook videos list response."""

    data: List[FacebookRawVideo] = Field(default_factory=list, description="List of videos")
    paging: Optional[FacebookPaging] = Field(default=None, description="Paging information")

    class Config:
        extra = "allow"  # Allow extra fields


class FacebookAPI:
    """Facebook Graph API wrapper for video data retrieval."""

    def __init__(self, access_token, parent=None, status_var=None):
        """
        Initialize the Facebook API wrapper.

        Args:
            access_token: Facebook API access token
            parent: Parent UI component for update callbacks
            status_var: Status variable for UI updates
        """
        self.access_token = access_token
        self.api_base_url = FB_API_BASE_URL
        self.parent = parent
        self.status_var = status_var
        self.logger = get_logger()

    def _make_request(self, endpoint, params=None):
        """
        Make a request to the Facebook Graph API with improved error handling.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            dict: API response data

        Raises:
            ValueError: If the API returns an error
        """
        if params is None:
            params = {}

        # Add access token to params
        params["access_token"] = self.access_token

        # Make request
        url = f"{self.api_base_url}{endpoint}"
        self.logger.log(f"Making request to: {url}")

        # Log params without showing token
        params_log = {k: ("[REDACTED]" if k == "access_token" else v) for k, v in params.items()}
        self.logger.log(f"With parameters: {params_log}")

        try:
            response = requests.get(url, params=params)
            self.logger.log(f"API Status Code: {response.status_code}")

            # Try to parse the response content
            try:
                content = response.json()
                # Log only a snippet of the response to avoid cluttering logs
                content_preview = json.dumps(content, indent=2)
                if len(content_preview) > 500:
                    content_preview = content_preview[:500] + "..."
                self.logger.log(f"API Response Preview: {content_preview}")
            except json.JSONDecodeError:
                self.logger.log(f"Raw Response (not JSON): {response.text[:500]}...")
                content = None

            # Check for HTTP errors
            response.raise_for_status()

            # If content is None or not parsed, try again
            if content is None:
                try:
                    content = response.json()
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse API response as JSON: {response.text[:500]}...")

            # Check for API errors in the response content
            if isinstance(content, dict) and "error" in content:
                # Parse error details with Pydantic
                try:
                    error_response = FacebookErrorResponse(**content)
                    error_message = f"API Error ({error_response.error.code}): {error_response.error.message}"
                    self.logger.log(
                        f"API Error: {error_response.error.code} {error_response.error.type} - "
                        f"{error_response.error.message}"
                    )
                    raise ValueError(error_message)
                except Exception:
                    # Fall back to manual extraction if Pydantic validation fails
                    error_details = content["error"]
                    error_message = error_details.get("message", "Unknown error")
                    error_code = error_details.get("code", "Unknown code")
                    error_type = error_details.get("type", "Unknown type")

                    error_str = f"API Error ({error_code}): {error_message}"
                    self.logger.log(f"API Error (manual parsing): {error_code} {error_type} - {error_message}")
                    raise ValueError(error_str)

            return content

        except requests.exceptions.HTTPError as e:
            self.logger.log(f"HTTP Error: {e}")

            # Try to extract error details from response
            error_message = f"HTTP Error: {e}"
            try:
                if hasattr(e, "response") and e.response is not None:
                    try:
                        error_content = e.response.json()
                        if "error" in error_content:
                            try:
                                error_response = FacebookErrorResponse(**error_content)
                                error_message = (
                                    f"API Error ({error_response.error.code}): " f"{error_response.error.message}"
                                )
                            except Exception:
                                # Manual extraction
                                error_details = error_content["error"]
                                error_message = error_details.get("message", "Unknown error")
                                error_code = error_details.get("code", "Unknown code")
                                error_message = f"API Error ({error_code}): {error_message}"
                        # No need to else here as error_message is already set with HTTP error
                    except (ValueError, json.JSONDecodeError):
                        if hasattr(e, "response") and e.response is not None:
                            self.logger.log(f"Response content: {e.response.text[:500]}")
            except Exception as parse_error:
                self.logger.log(f"Error parsing error response: {parse_error}")

            raise ValueError(error_message)

        except requests.exceptions.RequestException as e:
            self.logger.log(f"Request error: {e}")
            raise ValueError(f"Connection error: {e}")

        except Exception as e:
            self.logger.log(f"Unexpected error: {e}")
            raise ValueError(f"Unknown error: {e}")

    def test_api_versions(self, page_id) -> Tuple[bool, Optional[str], str]:
        """
        Test multiple API versions to find one that works.

        Args:
            page_id: Facebook page ID

        Returns:
            tuple: (success, version, message) where success is a boolean,
                  version is the working API version or None,
                  message is a descriptive message
        """
        api_versions = ["v16.0", "v17.0", "v18.0"]

        for version in api_versions:
            self.logger.log(f"Testing with API version: {version}")
            url = f"https://graph.facebook.com/{version}/{page_id}/videos"
            params = {"access_token": self.access_token, "limit": 1}

            try:
                response = requests.get(url, params=params)
                self.logger.log(f"Direct API Status Code with {version}: {response.status_code}")

                if response.status_code == 200:
                    # We don't need to use the content, just checking if the request was successful
                    self.logger.log(f"Success with version {version}")

                    # Update the API version
                    orig_version = self.api_base_url
                    self.api_base_url = f"https://graph.facebook.com/{version}/"
                    self.logger.log(f"Updated API base URL from {orig_version} to {self.api_base_url}")

                    return True, version, f"Successfully connected using API version {version}"
            except Exception as e:
                self.logger.log(f"Error with version {version}: {e}")

        # If all versions failed
        return False, None, "Failed to connect with all API versions. Check token permissions."

    def get_page_videos(self, page_id, limit=25, after=None):
        """
        Get videos for a Facebook page.

        Args:
            page_id: Facebook page ID
            limit: Maximum number of videos to fetch
            after: Pagination cursor

        Returns:
            FacebookVideosResponse: API response with video data
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
            "video_insights{total_video_views,total_video_impressions,total_video_view_time,"
            "total_video_views_by_follower_status,total_video_views_by_distribution_type,"
            "total_video_view_time_by_age_bucket_and_gender,total_video_view_time_by_region_id,"
            "total_video_view_time_by_distribution_type}",
        ]

        # Build params
        params = {"fields": ",".join(fields), "limit": limit}

        # Add pagination if present
        if after:
            params["after"] = after

        # Make request
        endpoint = f"{page_id}/videos"
        result = self._make_request(endpoint, params)

        # Validate and parse response using Pydantic model
        try:
            return FacebookVideosResponse(**result)
        except Exception as e:
            self.logger.log(f"Error parsing Facebook Videos Response: {e}")
            self.logger.log(f"Raw response: {json.dumps(result)[:500]}")
            raise ValueError(f"Error processing API response: {e}")

    def get_video_insights(self, video_id):
        """
        Get insights data for a specific video.

        Args:
            video_id: Facebook video ID

        Returns:
            FacebookVideoInsightsResponse: API response with insights data
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

        result = self._make_request(endpoint, params)

        # Validate and parse response using Pydantic model
        return FacebookVideoInsightsResponse(**result)

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

    # Test API versions if needed
    if "v" not in fb_api.api_base_url:
        success, version, message = fb_api.test_api_versions(page_id)
        if not success:
            logger.log(f"API version test failed: {message}")
            raise ValueError(message)
        else:
            logger.log(f"API version test succeeded: {message}")

    # Get videos with pagination
    videos = []
    after = None
    total_fetched = 0

    while total_fetched < max_videos:
        # Determine how many to fetch in this batch
        remaining = max_videos - total_fetched
        batch_limit = min(25, remaining)  # API limit is 25 per request

        try:
            # Fetch batch
            response = fb_api.get_page_videos(page_id, limit=batch_limit, after=after)

            if not response.data:
                break

            # Process videos in this batch
            batch_videos = response.data
            logger.log(f"Fetched {len(batch_videos)} videos (batch)")

            # Process each video
            for video in batch_videos:
                # Convert to dict from Pydantic model
                video_dict = video.dict()

                # Add to the list
                videos.append(video_dict)

            # Update counts
            total_fetched += len(batch_videos)
            logger.log(f"Fetched {total_fetched}/{max_videos} videos (total)")

            # Check for more pages
            if response.paging and response.paging.cursors and response.paging.cursors.after:
                after = response.paging.cursors.after
            else:
                break

        except Exception as e:
            logger.log(f"Error fetching video batch: {e}")
            raise ValueError(f"Error retrieving videos: {e}")

    # Return the data for processing
    logger.log(f"Completed retrieving {len(videos)} videos")
    return videos
