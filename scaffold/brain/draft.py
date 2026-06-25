"""Stage 3 — the draft. The ONLY creative step in the whole loop.

Calls Claude (Opus = the brain, mirroring the real topology) to compose a candidate reply
grounded in the assembled context, and to self-rate confidence + sensitivity. If no API key
is present it falls back to a deterministic mock so the demo runs for everyone with zero setup.

The brain has NO WhatsApp socket. It returns a Draft. It cannot send.
"""
import json
import os
import uuid

try:
    import anthropic
except ImportError:
    anthropic = None

from .seam import Draft

# Default to Opus for the brain — it's what we run in production. Override with WA_BRAIN_MODEL
# (e.g. claude-sonnet-4-6 / claude-haiku-4-5) to trade some quality for cost.
MODEL = os.environ.get("WA_BRAIN_MODEL", "claude-opus-4-8")

SYSTEM = (
    "You are the BRAIN of an autonomous WhatsApp assistant answering INBOUND messages from "
    "third parties (clients, suppliers, leads) on a business line. Draft a reply grounded ONLY "
    "in the provided context — never invent relationship history or make commitments you can't "
    "support. Then self-assess: set sensitive=true if the reply touches money, payments, "
    "commitments, legal, or health (these must never auto-send); rate confidence 0..1 on how "
    "sure you are the draft is correct and safe to send as-is."
)

# Structured output — the brain returns exactly these fields, no parsing guesswork.
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "intent": {"type": "string"},
        "sensitive": {"type": "boolean"},
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
    },
    "required": ["text", "intent", "sensitive", "confidence", "rationale"],
    "additionalProperties": False,
}


def compose_draft(inbound, ctx):
    data = (
        _llm_draft(inbound, ctx)
        if anthropic and os.environ.get("ANTHROPIC_API_KEY")
        else _mock_draft(inbound, ctx)
    )
    return Draft(
        draft_id=str(uuid.uuid4())[:8],
        thread_id=inbound.thread_id,
        to=inbound.sender,
        text=data["text"],
        intent=data["intent"],
        sensitive=data["sensitive"],
        confidence=data["confidence"],
        rationale=data["rationale"],
    )


def _llm_draft(inbound, ctx):
    client = anthropic.Anthropic()
    prompt = (
        f"CONTEXT:\n{json.dumps(ctx, indent=2)}\n\n"
        f"INBOUND from {inbound.sender}:\n{inbound.text!r}\n\n"
        "Compose the reply."
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": DRAFT_SCHEMA}},
    )
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


# --- mock fallback: deterministic, no API key needed -------------------------------------
# Keyword heuristics so the demo exercises all three governance lanes without a model call.
_SENSITIVE = ("invoice", "payment", "pay ", "refund", "price", "quote", "contract", "deposit")


def _mock_draft(inbound, ctx):
    t = inbound.text.lower()
    sensitive = any(k in t for k in _SENSITIVE)
    if sensitive:
        intent, confidence = "billing", 0.55
        text = f"Hi {ctx['name']}, thanks — let me check that and get right back to you."
    elif not ctx["known"]:
        intent, confidence = "unknown", 0.40          # unfamiliar sender → low confidence
        text = "Hi! Thanks for reaching out — could you tell me a bit more about what you need?"
    else:
        intent, confidence = "routine", 0.88          # known contact, clear ask → high confidence
        text = f"Hi {ctx['name']}, yes — happy to help with that. "
    return {
        "text": text,
        "intent": intent,
        "sensitive": sensitive,
        "confidence": confidence,
        "rationale": "[mock draft — set ANTHROPIC_API_KEY to use the real Opus brain]",
    }
