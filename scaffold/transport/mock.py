"""A mock transport so the whole loop runs end-to-end with NO WhatsApp pairing and NO risk.

Inbound: replays a scripted JSON inbox. Outbound: enforces GUARD 3 — it refuses to send
anything whose token doesn't verify-and-burn, then "sends" by printing. This is the dumb
transport: no model, no composing, just the wire contract.
"""
import json

from brain.seam import Inbound
from .base import Transport


class MockTransport(Transport):
    def __init__(self, inbox_path):
        self.inbox_path = inbox_path
        self.sent = []          # record of what actually reached the wire

    def receive(self):
        with open(self.inbox_path) as f:
            for m in json.load(f):
                yield Inbound(
                    sender=m["sender"],
                    text=m["text"],
                    thread_id=m["thread_id"],
                    timestamp=m["timestamp"],
                )

    def send(self, outbound, tokens):
        # GUARD 3: no valid, single-use, draft-bound token → no send.
        if not tokens.verify_and_burn(outbound.send_token, outbound.draft_id):
            print(f"  ⛔ REFUSED to {outbound.to}: invalid or reused token (draft {outbound.draft_id})")
            return False
        print(f"  📤 SENT to {outbound.to}: {outbound.text!r}")
        self.sent.append(outbound)
        return True
