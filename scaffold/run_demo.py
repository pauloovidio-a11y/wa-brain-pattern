#!/usr/bin/env python3
"""End-to-end demo of the brain/transport pattern — runs with NO WhatsApp pairing, NO API key.

    python run_demo.py            # run the loop over a scripted inbox
    python run_demo.py --review   # then drop into interactive operator review of held drafts

What you'll see: each inbound is drafted by the brain, routed by policy into a lane, and only
the auto_approve lane mints a token and reaches the (mock) wire. The guarded lanes stay in
shadow. Finally we forge a tokenless send to show the transport refuse it.
"""
import os
import sys

from brain.seam import Queue, Outbound
from brain.shadow import Shadow
from brain.tokens import TokenVault
from brain.loop import handle
from brain.approval import review_pending
from transport.mock import MockTransport

HERE = os.path.dirname(os.path.abspath(__file__))
CONTACTS = os.path.join(HERE, "sample_data", "contacts.json")
INBOX = os.path.join(HERE, "sample_data", "inbox.json")

LANE_ICON = {"auto_approve": "✅ auto", "shadow_only": "🕓 shadow", "operator_required": "🔒 operator"}


def main():
    transport = MockTransport(INBOX)
    shadow = Shadow()
    tokens = TokenVault()
    outbound = Queue()

    brain = "real Opus brain" if os.environ.get("ANTHROPIC_API_KEY") else "mock brain (no API key)"
    print(f"\nwa-brain-pattern demo · {brain}\n" + "=" * 70)

    # ── brain side: every inbound walks the governance loop ──────────────────────
    outcomes = []
    for inbound in transport.receive():
        outcomes.append(handle(
            inbound, contacts_path=CONTACTS, shadow=shadow, tokens=tokens, outbound_queue=outbound,
        ))

    print(f"\n{'INBOUND':<48} {'CONF':>5}  LANE")
    print("-" * 70)
    for o in outcomes:
        snippet = (o.inbound_text[:45] + "…") if len(o.inbound_text) > 46 else o.inbound_text
        print(f"{snippet:<48} {o.confidence:>5.2f}  {LANE_ICON[o.lane]}")

    # ── transport side: drain the outbound queue. Only auto-approved + tokened sends fire ──
    print("\nDISPATCH (transport verifies the token, then sends verbatim):")
    for ob in outbound.drain():
        transport.send(ob, tokens)

    # ── what the guards held back ────────────────────────────────────────────────
    held = shadow.pending()
    print(f"\nHELD FOR A HUMAN ({len(held)}): the brain drafted these but they never went to the wire")
    for d in held:
        why = "sensitive → operator_required" if d.sensitive else f"confidence {d.confidence:.2f} < threshold → shadow_only"
        print(f"  • to {d.to} ({d.intent}) — {why}")

    # ── prove the token gate: a forged, tokenless send is refused ─────────────────
    print("\nTOKEN-GATE CHECK (forging a send with no valid token):")
    transport.send(Outbound(to="+15550000002", text="(forged)", draft_id="nope", send_token="fake"), tokens)

    print("\n" + "=" * 70)
    print(f"reached the wire: {len(transport.sent)}   held by guards: {len(held)}")
    print("Capability is split from authority: the brain wrote every draft but sent nothing —")
    print("only an approved, token-bearing outbound reached the transport.\n")

    if "--review" in sys.argv:
        print("=" * 70 + "\nOPERATOR REVIEW (interactive):")
        review_pending(shadow, tokens, outbound)
        for ob in outbound.drain():
            transport.send(ob, tokens)


if __name__ == "__main__":
    main()
