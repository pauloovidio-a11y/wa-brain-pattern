"""GUARD 1 — shadow. A holding store for drafts the system is *considering*.

A draft in shadow is a candidate, nothing more. This is what lets you run the whole
pipeline in observe-only mode from day one: every inbound gets a full draft, you watch
quality accumulate, and nothing has gone out. Graduate lanes out of shadow as they prove
themselves — never ship straight past it on a stranger-facing line.
"""


class Shadow:
    def __init__(self):
        self._drafts = {}      # draft_id -> Draft
        self._lane = {}        # draft_id -> lane it was staged under

    def stage(self, draft, lane):
        self._drafts[draft.draft_id] = draft
        self._lane[draft.draft_id] = lane

    def get(self, draft_id):
        return self._drafts.get(draft_id)

    def pending(self, lane=None):
        """Drafts still awaiting a human (everything not auto-approved-and-sent)."""
        return [
            d for did, d in self._drafts.items()
            if lane is None or self._lane[did] == lane
        ]

    def discard(self, draft_id):
        self._drafts.pop(draft_id, None)
        self._lane.pop(draft_id, None)
