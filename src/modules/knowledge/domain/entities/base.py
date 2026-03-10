"""
Base Entity Model with Audit Trail

All domain entities extend from this base model to inherit
common audit fields for tracking creation, updates, and deletion.
"""
from datetime import datetime
from uuid import UUID, uuid4, NIL_UUID
from typing import Optional

from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    """
    Base model for all domain entities with full audit trail.
    
    Attributes:
        id: Unique identifier for the entity
        created_at: Timestamp when the entity was created
        created_by: UUID of the user who created the entity (defaults to NIL_UUID)
        updated_at: Timestamp when the entity was last updated
        updated_by: UUID of the user who last updated the entity
        deleted_at: Timestamp when the entity was soft-deleted (None if not deleted)
        deleted_by: UUID of the user who deleted the entity
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of creation"
    )
    created_by: UUID = Field(
        default=NIL_UUID,
        description="UUID of user who created this entity"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of last update"
    )
    updated_by: UUID = Field(
        default=NIL_UUID,
        description="UUID of user who last updated this entity"
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of soft deletion"
    )
    deleted_by: Optional[UUID] = Field(
        default=None,
        description="UUID of user who deleted this entity"
    )
    
    def is_deleted(self) -> bool:
        """Check if the entity has been soft-deleted."""
        return self.deleted_at is not None
    
    def mark_deleted(self, deleted_by: UUID = NIL_UUID) -> None:
        """Mark the entity as soft-deleted."""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
    
    def mark_updated(self, updated_by: UUID = NIL_UUID) -> None:
        """Update the updated_at timestamp and updated_by field."""
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-01-15T10:30:00",
                "created_by": "00000000-0000-0000-0000-000000000000",
                "updated_at": "2024-01-15T10:30:00",
                "updated_by": "00000000-0000-0000-0000-000000000000",
                "deleted_at": None,
                "deleted_by": None,
            }
        }