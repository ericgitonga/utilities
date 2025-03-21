"""
Video data models for the Facebook Video Data Tool application.
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator, root_validator


class VideoInsights(BaseModel):
    """Pydantic model for video insights metrics."""

    total_video_views: Optional[int] = Field(default=0, description="Total number of video views")
    total_video_impressions: Optional[int] = Field(default=0, description="Total number of video impressions")
    total_video_view_time: Optional[int] = Field(default=0, description="Total view time in milliseconds")
    total_video_complete_views: Optional[int] = Field(default=0, description="Number of complete views")
    total_video_30s_views: Optional[int] = Field(default=0, description="Number of 30-second views")

    # Allow additional fields for other insight metrics
    class Config:
        extra = "allow"


class VideoData(BaseModel):
    """Pydantic model for Facebook video data."""

    id: str = Field(..., description="Facebook video ID")
    title: Optional[str] = Field(default="", description="Video title")
    description: Optional[str] = Field(default="", description="Video description")
    created_time: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_time: Optional[datetime] = Field(default=None, description="Last update timestamp")
    length: Optional[int] = Field(default=0, description="Video duration in seconds")
    views: int = Field(default=0, description="Number of video views")
    comments_count: int = Field(default=0, description="Number of comments")
    likes_count: int = Field(default=0, description="Number of likes")
    shares_count: int = Field(default=0, description="Number of shares")
    saves_count: Optional[int] = Field(default=0, description="Number of saves")
    reach: Optional[int] = Field(default=0, description="Video reach count")
    avg_watch_time: Optional[float] = Field(default=0, description="Average watch time in seconds")
    total_watch_time: Optional[float] = Field(default=0, description="Total watch time in seconds")
    views_from_followers: Optional[int] = Field(default=0, description="Views from page followers")
    views_from_non_followers: Optional[int] = Field(default=0, description="Views from non-followers")
    follower_percentage: Optional[float] = Field(default=0, description="Percentage of views from followers")
    link_clicks: Optional[int] = Field(default=0, description="Number of link clicks")
    permalink_url: Optional[str] = Field(default="", description="Permanent URL to the video")
    insights: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Raw insights data")

    # Store raw data (excluded from serialization)
    _raw_data: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    @validator("created_time", "updated_time", pre=True)
    def parse_datetime(cls, value):
        """Parse datetime from string if needed."""
        if isinstance(value, str):
            try:
                return pd.to_datetime(value)
            except ValueError:
                return None
        return value

    @root_validator(pre=True)
    def extract_counts(cls, values):
        """Extract counts from nested API response structures."""
        if "comments" in values and isinstance(values["comments"], dict):
            summary = values.get("comments", {}).get("summary", {})
            values["comments_count"] = summary.get("total_count", 0)

        if "likes" in values and isinstance(values["likes"], dict):
            summary = values.get("likes", {}).get("summary", {})
            values["likes_count"] = summary.get("total_count", 0)

        if "shares" in values and isinstance(values["shares"], dict):
            values["shares_count"] = values.get("shares", {}).get("count", 0)

        if "saved" in values and isinstance(values["saved"], dict):
            summary = values.get("saved", {}).get("summary", {})
            values["saves_count"] = summary.get("total_count", 0)

        # Process insights if present
        if "video_insights" in values and isinstance(values["video_insights"], dict):
            insights_data = values.get("video_insights", {}).get("data", [])

            for insight in insights_data:
                name = insight.get("name")
                values_list = insight.get("values", [])

                if not values_list:
                    continue

                value = values_list[0].get("value")

                if name == "total_video_view_time":
                    # Convert to seconds
                    values["total_watch_time"] = value / 1000 if isinstance(value, (int, float)) else 0
                    if values.get("views", 0) > 0:
                        values["avg_watch_time"] = values["total_watch_time"] / values["views"]

                elif name == "total_video_views_by_follower_status" and isinstance(value, dict):
                    values["views_from_followers"] = value.get("follower", 0)
                    values["views_from_non_followers"] = value.get("non_follower", 0)

                # Store raw insight
                if "insights" not in values:
                    values["insights"] = {}
                values["insights"][name] = value

        # Calculate follower percentage
        if values.get("views", 0) > 0 and values.get("views_from_followers", 0) > 0:
            values["follower_percentage"] = (values["views_from_followers"] / values["views"]) * 100

        # Store raw data for future reference
        values["_raw_data"] = {k: v for k, v in values.items()}

        return values

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

    def get_raw_data(self) -> Dict[str, Any]:
        """Get the original raw data."""
        return self._raw_data

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
            "reach": self.reach,
            "comments_count": self.comments_count,
            "likes_count": self.likes_count,
            "shares_count": self.shares_count,
            "saves_count": self.saves_count,
            "link_clicks": self.link_clicks,
            "permalink_url": self.permalink_url,
            "avg_watch_time": self.avg_watch_time,
            "total_watch_time": self.total_watch_time,
            "views_from_followers": self.views_from_followers,
            "views_from_non_followers": self.views_from_non_followers,
            "follower_percentage": self.follower_percentage,
        }

        # Add insights
        if self.insights:
            data.update(self.insights)

        return data

    class Config:
        # Allow extra fields in input data
        extra = "ignore"


class VideoDataCollection(BaseModel):
    """Collection of VideoData objects with analysis capabilities."""

    videos: List[VideoData] = Field(default_factory=list, description="List of videos")

    @classmethod
    def from_api_response(cls, videos_data: List[Dict[str, Any]]) -> "VideoDataCollection":
        """Create a collection from API response data."""
        if not videos_data:
            return cls(videos=[])

        video_models = [VideoData.parse_obj(video) for video in videos_data]
        return cls(videos=video_models)

    def add_videos(self, videos_data: List[Dict[str, Any]]):
        """Add videos to the collection."""
        for video_data in videos_data:
            self.videos.append(VideoData.parse_obj(video_data))

    def clear(self):
        """Clear all videos from the collection."""
        self.videos = []

    def get_video(self, index: int) -> Optional[VideoData]:
        """Get video by index."""
        if 0 <= index < len(self.videos):
            return self.videos[index]
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate collection statistics."""
        total_videos = len(self.videos)

        if total_videos == 0:
            return {
                "total_videos": 0,
                "total_views": 0,
                "average_views": 0,
                "total_engagement": 0,
                "average_engagement": 0,
                "average_watch_time": 0,
                "total_watch_time": 0,
            }

        total_views = sum(video.views for video in self.videos)
        total_comments = sum(video.comments_count for video in self.videos)
        total_likes = sum(video.likes_count for video in self.videos)
        total_shares = sum(video.shares_count for video in self.videos)
        total_saves = sum(video.saves_count for video in self.videos)

        # Watch time metrics
        total_watch_time = sum(video.total_watch_time for video in self.videos)
        videos_with_watch_time = sum(1 for video in self.videos if video.total_watch_time > 0)
        average_watch_time = total_watch_time / videos_with_watch_time if videos_with_watch_time > 0 else 0

        # Engagement includes reactions, comments, shares, and saves
        total_engagement = total_comments + total_likes + total_shares + total_saves

        # Reach
        total_reach = sum(video.reach for video in self.videos)

        return {
            "total_videos": total_videos,
            "total_views": total_views,
            "average_views": total_views / total_videos,
            "total_reach": total_reach,
            "average_reach": total_reach / total_videos if total_videos > 0 else 0,
            "total_engagement": total_engagement,
            "average_engagement": total_engagement / total_videos,
            "total_comments": total_comments,
            "total_likes": total_likes,
            "total_shares": total_shares,
            "total_saves": total_saves,
            "total_watch_time": total_watch_time,
            "average_watch_time": average_watch_time,
        }

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert collection to pandas DataFrame."""
        import pandas as pd

        data = [video.dict() for video in self.videos]
        return pd.DataFrame(data)

    def to_list(self) -> List[Dict[str, Any]]:
        """Convert collection to list of dictionaries."""
        return [video.dict() for video in self.videos]

    def get_raw_data(self) -> List[Dict[str, Any]]:
        """Get raw API data for all videos."""
        return [video.get_raw_data() for video in self.videos]

    def __len__(self) -> int:
        """Get number of videos in collection."""
        return len(self.videos)
