"""The autonomy dial — which lane a draft falls into.

This is where the loop's threshold lives, and the loop NEVER changes — only this verdict
moves. Contributed framing from the RoboNuggets community (Xavi Digi): a confidence
threshold is a clean way to auto-demote a lane back to shadow when the model isn't sure.

Lanes:
  operator_required — never auto-sends; a human must approve (default for anything sensitive)
  shadow_only       — staged for review; not sent (the model wasn't confident enough)
  auto_approve      — mints a token and goes to the wire, no human in the loop
"""

# Per-deployment knob. Raise it to demand more confidence before auto-sending.
CONFIDENCE_THRESHOLD = 0.75


def policy(draft, threshold=CONFIDENCE_THRESHOLD):
    if draft.sensitive:
        return "operator_required"          # money / commitments / legal / health → always a human
    if draft.confidence < threshold:
        return "shadow_only"                # not sure enough → demote to review (Xavi's lane)
    return "auto_approve"
