"""The governance loop, wired together: one inbound → a routed outcome.

  inbound → assemble_context → compose_draft → policy → shadow → (auto?) approve → token → send

The brain never touches the wire. Auto-approved drafts get a token and go to the outbound
queue; guarded drafts (operator_required / shadow_only) stay in shadow for human review.
"""
from dataclasses import dataclass

from .context import assemble_context
from .draft import compose_draft
from .policy import policy
from .approval import approve


@dataclass
class Outcome:
    inbound_text: str
    to: str
    intent: str
    confidence: float
    lane: str
    sent: bool          # did this reach the outbound queue, or get held for a human?


def handle(inbound, *, contacts_path, shadow, tokens, outbound_queue, health=None):
    ctx = assemble_context(inbound, contacts_path)          # ② gather, don't invent
    draft = compose_draft(inbound, ctx)                     # ③ the only creative step
    lane = policy(draft)                                    # the autonomy dial

    # v3 — transport circuit breaker (Graeme C's point): if the number's transport is degraded,
    # HOLD every draft — even an auto-approve one. The operator was already alerted by the
    # heartbeat, so this is "pause before the client notices," not "go quiet on a client."
    if health is not None and not health.is_sendable(draft.to):
        shadow.stage(draft, "transport_paused")
        return _outcome(inbound, draft, lane="transport_paused", sent=False)

    shadow.stage(draft, lane)                               # ④ GUARD 1 — staged, not sent

    sent = False
    if lane == "auto_approve":
        approve(draft, tokens, outbound_queue)             # ⑤+⑥ approve + mint token
        shadow.discard(draft.draft_id)
        sent = True                                         # ⑦ transport will verify + send

    return _outcome(inbound, draft, lane=lane, sent=sent)


def _outcome(inbound, draft, *, lane, sent):
    return Outcome(
        inbound_text=inbound.text,
        to=draft.to,
        intent=draft.intent,
        confidence=draft.confidence,
        lane=lane,
        sent=sent,
    )
