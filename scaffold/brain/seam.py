"""The seam: the two message shapes that cross the queue, plus the queue itself.

The brain and the transport share NOTHING but this. The brain produces Drafts and
(after approval) Outbounds; the transport produces Inbounds and consumes Outbounds.
Neither imports the other.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Inbound:
    """A message from a stranger, normalized by the transport. No intelligence here."""
    sender: str          # the stranger's WhatsApp id (phone / JID)
    text: str
    thread_id: str
    timestamp: str
    media: Optional[str] = None


@dataclass
class Draft:
    """A candidate reply composed by the brain. NOT sent — staged in shadow first."""
    draft_id: str
    thread_id: str
    to: str
    text: str
    intent: str          # the brain's classification of what the stranger wants
    sensitive: bool      # touches money / commitments / legal / health → never auto-send
    confidence: float    # the brain's self-rated 0..1 (drives Xavi's threshold lane)
    rationale: str = ""


@dataclass
class Outbound:
    """An approved draft on its way to the wire. The send_token is the whole game:
    the transport refuses to send anything without a valid, single-use, draft-bound token."""
    to: str
    text: str
    draft_id: str
    send_token: str


class Queue:
    """The only contract between brain and transport. Deliberately tiny."""
    def __init__(self):
        self._items = []

    def put(self, item):
        self._items.append(item)

    def drain(self):
        items, self._items = self._items, []
        return items

    def __len__(self):
        return len(self._items)
