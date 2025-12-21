"""
Object model.
"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from pyrox.models.division import Division


class EventDetails(BaseModel):
    """Details for a Hyrox event"""

    # the date the event took place
    date: datetime
    # the divisions for the event
    divisions: list[Division]


class Event(BaseModel):
    """A Hyrox event"""

    # the name of the event
    name: str
    # the link to the event page
    url: HttpUrl

    # the details for the event
    details: EventDetails = Field(
        default_factory=lambda: EventDetails(date=datetime.now(), divisions=[])
    )

    @property
    def canonical_name(self) -> str:
        """Get the canonical name for the event."""
        return Event.canonicalize(self.name)

    @staticmethod
    def canonicalize(name: str) -> str:
        """Canonicalize an event name."""
        return "_".join(name.lower().removeprefix("hyrox").strip().split())
