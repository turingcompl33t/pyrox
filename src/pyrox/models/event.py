"""
Object model.
"""

from datetime import datetime

from pydantic import BaseModel, HttpUrl


class Event(BaseModel):
    """A Hyrox event"""

    # the name of the event
    name: str
    # the date the event took place
    date: datetime
    # the link to the event page
    url: HttpUrl

    @property
    def canonical_name(self) -> str:
        """Get the canonical name for the event."""
        return Event.canonicalize(self.name)

    @staticmethod
    def canonicalize(name: str) -> str:
        """Canonicalize an event name."""
        return "_".join(name.lower().removeprefix("hyrox").strip().split())
