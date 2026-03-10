"""
Data Source Entity

Represents external data sources from which documents are ingested.
"""
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseModel


class DataSourceType(str, Enum):
    """Enumeration of supported data source types."""
    
    GOOGLE_DRIVE = "google_drive"
    ONE_DRIVE = "one_drive"
    MS_SHARE_POINT = "ms_share_point"
    LOCAL_FILESYSTEM = "local_filesystem"
    WEB = "web"
    API = "api"
    
    @classmethod
    def default(cls) -> "DataSourceType":
        """Return the default data source type."""
        return cls.GOOGLE_DRIVE


class DataSource(BaseModel):
    """
    Data Source entity representing an external content source.
    
    Attributes:
        name: The type of data source (enum)
        description: Optional human-readable description
        config: Optional JSON configuration for the data source connection
        is_active: Whether this data source is currently active
    """
    
    name: DataSourceType = Field(
        default=DataSourceType.default(),
        description="Type of data source"
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the data source"
    )
    config: Optional[dict] = Field(
        default=None,
        description="Configuration for connecting to the data source"
    )
    is_active: bool = Field(
        default=True,
        description="Whether this data source is active"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "google_drive",
                "description": "Company Google Drive shared folder",
                "config": {
                    "folder_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OE"
                },
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "created_by": "00000000-0000-0000-0000-000000000000",
                "updated_at": "2024-01-15T10:30:00",
                "updated_by": "00000000-0000-0000-0000-000000000000",
            }
        }