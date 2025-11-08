from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import uuid
from decimal import Decimal

class Book(BaseModel):
    book_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: List[Literal[
        "fiction", "non-fiction", "fantasy", "sci-fi", "romance",
        "mystery", "thriller", "biography", "history", "self-help"
    ]] = Field(default_factory=list)
    status: Literal["available", "borrowed"] = "available"
    stock: int = Field(..., ge=0, description="Cantidad de copias disponibles en inventario")
    average_rating: Decimal = Field(default=Decimal("0.0"), ge=0, le=5)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Hobbit",
                "description": "A fantasy novel by J.R.R. Tolkien",
                "genre": ["fantasy", "adventure"],
                "status": "available",
                "stock": 10,
                "average_rating": 4.8
            }
        }

    def update_timestamp(self):
        """Actualiza el campo updated_at a la hora actual en UTC."""
        self.updated_at = datetime.utcnow().isoformat()

    @field_validator("genre")
    def check_genre_not_empty(cls, v):
        if not v:
            raise ValueError("Debe incluir al menos un género.")
        return v
