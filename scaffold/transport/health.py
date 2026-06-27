"""v3 — transport health. The part that decides whether the agent survives production.

Graeme C (RoboNuggets) nailed the gap in v1/v2: the governance loop can be perfect and still
fail, because the TRANSPORT isn't running. Sessions drop, tokens expire, numbers get flagged.
"Your governance loop is perfect, it's just not running — and you find out when a client does,
not when you do." The fix isn't more brain; it's a heartbeat per number that auto-pauses the bot
the second a session degrades and pings the operator before the client notices the silence.

This module is that circuit breaker. It tracks per-number transport health from heartbeats; the
loop checks `is_sendable(number)` BEFORE any send, so a degraded number HOLDS its drafts (even
auto-approve ones) and the operator is alerted — instead of the bot going quiet on a real client.

In production the heartbeat is a periodic probe of the linked-device client: is the session alive,
is the token still valid, is the number unflagged? Here it's driven by explicit `heartbeat()`
calls so the demo is deterministic.
"""
from dataclasses import dataclass
from enum import Enum


class Health(Enum):
    HEALTHY = "healthy"     # session alive, token valid, number clean → safe to send
    DEGRADED = "degraded"   # soft warning (slow heartbeat, token near expiry) → pause + alert
    DOWN = "down"           # hard failure (session dropped, number flagged) → pause + alert


@dataclass
class NumberState:
    number: str
    health: Health = Health.HEALTHY
    reason: str = ""


class HealthMonitor:
    """Per-number transport circuit breaker. Only HEALTHY numbers are sendable."""

    def __init__(self, alert):
        # alert: callable(number, health, reason) — reaches the operator (Telegram DM, page, CLI…)
        self._state = {}        # number -> NumberState
        self._alert = alert

    def heartbeat(self, number, health, reason=""):
        """Record a heartbeat for a number's transport session. Transitioning OUT of HEALTHY
        fires a single operator alert — before the client notices the silence."""
        st = self._state.setdefault(number, NumberState(number))
        was_healthy = st.health == Health.HEALTHY
        st.health = health
        st.reason = "" if health == Health.HEALTHY else (reason or "transport heartbeat failed")
        # Alert on the edge into a bad state only — don't spam every beat.
        if health != Health.HEALTHY and was_healthy:
            self._alert(number, health, st.reason)
        return st.health

    def is_sendable(self, number):
        """True only when the number's transport is HEALTHY. Unknown numbers default healthy."""
        st = self._state.get(number)
        return st is None or st.health == Health.HEALTHY

    def status(self, number):
        st = self._state.get(number)
        return st.health if st else Health.HEALTHY
