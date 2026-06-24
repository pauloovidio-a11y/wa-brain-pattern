# Adapt — wiring the pattern onto your transport

This is a **documentation skill**, so what follows is *interfaces and responsibilities*, not
runnable code. The shapes are deliberately language-agnostic — fill them in whatever stack
your transport already uses. The goal is to make the seam and the guards explicit so you
don't accidentally collapse the pattern while building.

---

## Step 0 — bring your own transport
Do not build a WhatsApp client. Run an existing linked-device one and treat it as the
**transport tier**:

- **[Rich627/whatsapp-claude-plugin](https://github.com/Rich627/whatsapp-claude-plugin)** —
  community reference. Baileys, no Business API, no keys.
- `lharries/whatsapp-mcp` · `jlucaso1/whatsapp-mcp-ts` — MCP-style alternatives.

You will adapt it so that instead of replying inline, it (a) pushes inbound onto a queue and
(b) only sends outbound that carries a valid token. Everything else below is the brain.

---

## The seam — two message shapes

```
inbound  = { from, text, media?, timestamp, thread_id }
outbound = { to, text, draft_id, send_token }
```

Keep the queue the *only* thing the two tiers share. No shared database the brain can write
sends into; no direct function call from brain to transport. Just these two envelopes
crossing a queue/outbox.

---

## Brain-layer responsibilities (stub interfaces)

These are the functions the brain process needs. Signatures describe *responsibility*, not
implementation.

```
on_inbound(envelope) -> void
    # entry point. Pulls one inbound envelope off the queue and runs the loop.
    ctx   = assemble_context(envelope)
    draft = compose_draft(envelope, ctx)
    stage_to_shadow(draft)            # NEVER send here

assemble_context(envelope) -> Context
    # GUARD-FREE but critical. Gather, do not invent:
    #   - contact_memory(thread_id): prior messages, commitments, status, open threads
    #   - enrichment(from): domain facts (account type, entitlements, history)
    # Return a Context the draft step can ground in. No model call required to gather facts.

compose_draft(envelope, ctx) -> Draft
    # The ONLY creative step. Calls the model with ctx. Returns a Draft:
    #   { draft_id, thread_id, to, text, rationale? }
    # The brain has NO whatsapp socket. It cannot send. It can only return a Draft.

stage_to_shadow(draft) -> void
    # Persist the draft to a holding store, surfaced to the operator. Not sent.
```

## Guard responsibilities (the part worth your time)

```
approval_bridge:
    # operator <-> system. Reaches the operator wherever they already are
    # (Telegram DM, CLI, web button, their own number).
    on_approve(draft_id):
        token = issue_send_token(draft_id)        # single-use, draft-bound
        enqueue_outbound({ to, text, draft_id, send_token: token })
    on_edit(draft_id, new_text):
        update draft text; then treat as on_approve
    on_veto(draft_id, reason?):
        drop draft; optionally feed reason back into contact_memory

issue_send_token(draft_id) -> Token
    # mint a token valid for exactly ONE send of exactly THIS draft.
    # store it so the transport can verify-and-burn it.

# --- transport side (adapt your chosen client) ---
transport.on_outbound(envelope):
    if not verify_and_burn(envelope.send_token, envelope.draft_id):
        reject            # no valid token => no send. This is GUARD 3.
    whatsapp_send(envelope.to, envelope.text)     # verbatim. no templating, no regen.
```

---

## Autonomy lanes
Make the approval step policy-driven so you can move the threshold without touching the agent:

```
policy(envelope, draft) -> "shadow_only" | "auto_approve" | "operator_required"
```

- Start **everything** at `shadow_only`.
- Graduate specific (contact, intent) pairs to `auto_approve` only after their drafts are
  consistently good.
- Keep high-stakes lanes (anything involving money, commitments, sensitive topics) at
  `operator_required` indefinitely.

The loop never changes — only what `policy()` returns.

---

## Checklist before you point it at a real number

- [ ] Brain process has **no** WhatsApp send capability of any kind.
- [ ] Transport **rejects** any outbound without a valid, draft-bound, single-use token.
- [ ] Every draft lands in **shadow** first; nothing auto-sends on first run.
- [ ] Approval surface is somewhere the operator **actually looks**.
- [ ] Context is **assembled before** drafting (no empty-context hallucinated history).
- [ ] `policy()` starts at `shadow_only` for all lanes.

If all six hold, you can grant the agent real authority over a stranger-facing line and still
reason about exactly what happens when something fails.
