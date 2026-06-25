"""The transport interface. Carries bytes, stays dumb.

A real transport owns the WhatsApp session (linked-device, e.g. Baileys / whatsapp-web.js
via Rich627/whatsapp-claude-plugin). It does exactly two things:
  - receive()  : pull inbound messages off the wire, normalize them to Inbound envelopes
  - send()     : send an approved, token-bearing Outbound — verbatim, AFTER verifying the token

It NEVER composes text and it has NO model. Swap MockTransport for a real one and the brain
above is unchanged.
"""
from abc import ABC, abstractmethod


class Transport(ABC):
    @abstractmethod
    def receive(self):
        """Yield Inbound envelopes from the wire."""

    @abstractmethod
    def send(self, outbound, tokens):
        """Verify outbound.send_token against tokens, then send verbatim. Refuse if invalid."""
