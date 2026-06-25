"""GUARD 2 — the approval bridge. Operator ↔ system (never agent ↔ stranger).

On approval, mint a single-use token (guard 3) and enqueue the outbound. The bridge can be
anything that reaches the operator — a Telegram DM, a web button, a CLI. Here it's a CLI.

`approve()` is the shared primitive. The auto_approve lane calls it with no human; the
operator calls it via `review_pending()` for the guarded lanes.
"""
from .seam import Outbound


def approve(draft, tokens, outbound_queue):
    """Mint a draft-bound token and put the approved outbound on the wire-bound queue."""
    token = tokens.issue(draft.draft_id)
    outbound_queue.put(Outbound(to=draft.to, text=draft.text, draft_id=draft.draft_id, send_token=token))


def review_pending(shadow, tokens, outbound_queue):
    """Interactive operator review of everything the guards held back. Approve / edit / veto."""
    pending = shadow.pending()
    if not pending:
        print("Nothing pending review. Every draft auto-sent or was already handled.")
        return

    for draft in list(pending):
        print("\n" + "─" * 70)
        print(f"to: {draft.to}   intent: {draft.intent}   confidence: {draft.confidence:.2f}"
              f"   sensitive: {draft.sensitive}")
        print(f"draft: {draft.text}")
        choice = input("[a]pprove  [e]dit  [v]eto  [s]kip > ").strip().lower()
        if choice == "a":
            approve(draft, tokens, outbound_queue)
            shadow.discard(draft.draft_id)
            print("  ✓ approved — token minted, queued to send")
        elif choice == "e":
            draft.text = input("  new text > ").strip() or draft.text
            approve(draft, tokens, outbound_queue)
            shadow.discard(draft.draft_id)
            print("  ✓ edited + approved — queued to send")
        elif choice == "v":
            shadow.discard(draft.draft_id)
            print("  ✗ vetoed — dropped")
        else:
            print("  · skipped — stays pending")
