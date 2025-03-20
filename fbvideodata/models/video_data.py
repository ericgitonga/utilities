"""
Video data models for the Facebook Video Data Tool application.
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional


class VideoData:
    """Model class for Facebook video data."""

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize VideoData from API response.

        Args:
            data: Dictionary containing video data from Facebook API
        """
        self.id = data.get("id", "")
        self.title = data.get("title", "")
        self.description = data.get("description", "")

        # Process timestamps
        self.created_time = self._parse_timestamp(data.get("created_time", ""))
        self.updated_time = self._parse_timestamp(data.get("updated_time", ""))

        # Metrics
        self.length = data.get("length", 0)
        self.views = data.get("views", 0)
        self.comments_count = data.get("comments_count", 0)
        self.likes_count = data.get("likes_count", 0)
        self.shares_count = data.get("shares_count", 0)

        # URL
        self.permalink_url = data.get("permalink_url", "")

        # Insights
        self.insights = {}
        for key, value in data.items():
            if key.startswith("total_"):
                self.insights[key] = value

        # Store the original data
        self._raw_data = data

    def _parse_timestamp(self, timestamp: str) -> Optional[datetime]:
        """
        Parse ISO timestamp string into datetime object.

        Args:
            timestamp: ISO format timestamp string

        Returns:
            datetime: Parsed datetime or None if parsing fails
        """
        if not timestamp:
            return None

        try:
            return pd.to_datetime(timestamp)
        except ValueError:
            return None

    @property
    def created_time_formatted(self) -> str:
        """Get formatted created time string."""
        if self.created_time:
            return self.created_time.strftime("%Y-%m-%d %H:%M:%S")
        return ""

    @property
    def updated_time_formatted(self) -> str:
        """Get formatted updated time string."""
        if self.updated_time:
            return self.updated_time.strftime("%Y-%m-%d %H:%M:%S")
        return ""

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.length:
            return "0:00"

        minutes = self.length // 60
        seconds = self.length % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def display_title(self) -> str:
        """Get display title, falling back to description snippet if title is missing."""
        if self.title:
            return self.title

        if self.description:
            # Use first 50 characters of description
            if len(self.description) > 50:
                return f"{self.description[:50]}..."
            return self.description

        return "Untitled"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for display or export.

        Returns:
            dict: Dictionary with video data
        """
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_time": self.created_time_formatted,
            "updated_time": self.updated_time_formatted,
            "length": self.length,
            "duration": self.duration_formatted,
            "views": self.views,
            "comments_count": self.comments_count,
            "likes_count": self.likes_count,
            "shares_count": self.shares_count,
            "permalink_url": self.permalink_url,
        }

        # Add insights
        data.update(self.insights)

        return data

    def get_raw_data(self) -> Dict[str, Any]:
        """
        Get the original raw data.

        Returns:
            dict: Original API response data
        """
        return self._raw_data


class VideoDataCollection:
    """Collection of VideoData objects with analysis capabilities."""

    def __init__(self, videos: List[Dict[str, Any]] = None):
        """
        Initialize VideoDataCollection.

        Args:
            videos: List of video data dictionaries from Facebook API
        """
        self.videos = []

        if videos:
            self.add_videos(videos)

    def add_videos(self, videos: List[Dict[str, Any]]):
        """
        Add videos to the collection.

        Args:
            videos: List of video data dictionaries from Facebook API
        """
        for video_data in videos:
            self.videos.append(VideoData(video_data))

    def clear(self):
        """Clear all videos from the collection."""
        self.videos = []

    def get_video(self, index: int) -> Optional[VideoData]:
        """
        Get video by index.

        Args:
            index: Index of the video

        Returns:
            VideoData: Video data at the specified index or None if index is invalid
        """
        if 0 <= index < len(self.videos):
            return self.videos[index]
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate collection statistics.

        Returns:
            dict: Dictionary with statistics
        """
        total_videos = len(self.videos)

        if total_videos == 0:
            return {
                "total_videos": 0,
                "total_views": 0,
                "average_views": 0,
                "total_engagement": 0,
                "average_engagement": 0,
            }

        total_views = sum(video.views for video in self.videos)
        total_comments = sum(video.comments_count for video in self.videos)
        total_likes = sum(video.likes_count for video in self.videos)
        total_shares = sum(video.shares_count for video in self.videos)

        total_engagement = total_comments + total_likes + total_shares

        return {
            "total_videos": total_videos,
            "total_views": total_views,
            "average_views": total_views / total_videos,
            "total_engagement": total_engagement,
            "average_engagement": total_engagement / total_videos,
            "total_comments": total_comments,
            "total_likes": total_likes,
            "total_shares": total_shares,
        }

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert collection to pandas DataFrame.

        Returns:
            DataFrame: DataFrame with video data
        """
        data = [video.to_dict() for video in self.videos]
        return pd.DataFrame(data)

    def to_list(self) -> List[Dict[str, Any]]:
        """
        Convert collection to list of dictionaries.

        Returns:
            list: List of video data dictionaries
        """
        return [video.to_dict() for video in self.videos]

    def get_raw_data(self) -> List[Dict[str, Any]]:
        """
        Get raw API data for all videos.

        Returns:
            list: List of original API response dictionaries
        """
        return [video.get_raw_data() for video in self.videos]

    def __len__(self) -> int:
        """Get number of videos in collection."""
        return len(self.videos)
