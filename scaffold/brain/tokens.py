"""GUARD 3 — the outbound token gate.

A single-use, draft-bound send token is what makes "approved" precise: *this exact text,
to this exact person, once.* The transport refuses to send any outbound that doesn't carry
a valid token, and each token verifies-and-burns — so it can't be replayed to re-send.

A global "sending is enabled" flag would gate WHETHER the system can send, not WHAT it sends.
Bind the token to the draft.
"""
import secrets


class TokenVault:
    def __init__(self):
        self._live = {}        # token -> draft_id

    def issue(self, draft_id):
        token = secrets.token_urlsafe(16)
        self._live[token] = draft_id
        return token

    def verify_and_burn(self, token, draft_id):
        """True exactly once per (token, draft) pair; False on reuse, forgery, or mismatch."""
        if self._live.get(token) != draft_id:
            return False
        del self._live[token]      # burn — no replay
        return True
