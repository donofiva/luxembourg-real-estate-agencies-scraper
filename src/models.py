from dataclasses import dataclass
from typing import Optional
import re
import hashlib


@dataclass
class Agency:
    """Real estate agency model with contact information."""

    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    detail_url: Optional[str] = None
    unique_id: Optional[str] = None
    is_active: bool = True

    def __post_init__(self):
        if self.unique_id is None:
            self.unique_id = self._generate_unique_id()

    def _generate_unique_id(self) -> str:
        """Generate unique identifier from name and location."""
        base_string = f"{self.name}|{self.location or ''}"
        normalized = re.sub(r"[^a-zA-Z0-9]", "", base_string.lower())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        """Convert agency to dictionary format."""
        return {
            "unique_id": self.unique_id,
            "name": self.name,
            "location": self.location,
            "description": self.description,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "detail_url": self.detail_url,
            "is_active": self.is_active,
        }
