# Topology — why split the brain from the transport

The whole pattern rests on one decision: **the process that thinks and the process that
sends are different processes, and they share only a queue.** This document explains why
that separation is worth the extra moving part.

## The default (and why it fails for strangers)

Most WhatsApp-on-LLM setups are a single process: it holds the WhatsApp session *and* calls
the model *and* sends whatever the model returns. For talking to yourself, that is fine —
you are the only human who ever sees the output, and you can just not act on a bad message.

The moment the other end is a **stranger** — a client, a supplier, a lead — three things
become unacceptable:

1. The model can promise something on your behalf, and it goes out instantly.
2. A crafted inbound message (prompt injection) can steer the model into sending.
3. A model restart, an upgrade, or a crash takes the WhatsApp session down with it.

A fused process cannot fix any of these without bolting guards onto the *inside* of the
same thing that has both the model and the socket — which is exactly the surface you are
trying to contain.

## The split

```
   THE BRAIN  (Claude Code · Opus)          THE TRANSPORT  (linked-device client)
   reasons · remembers · drafts             carries bytes · stays dumb
   no WhatsApp socket                        no model, no judgment
                       \                    /
                        \                  /
                         shared queue / outbox
                         the ONLY thing they share
```

- **Brain:** consumes inbound from the queue, assembles context, drafts a reply, writes the
  draft to shadow. It has no path to the WhatsApp network at all.
- **Transport:** owns the WhatsApp session (linked device via Baileys / WhatsApp Web). It
  pushes inbound onto the queue and pulls *approved, token-bearing* drafts off it to send,
  verbatim. It never composes text.

## What the split buys you

### 1. Capability is split from authority
The brain has the *capability* to write words but no *authority* to send them. The transport
has the *authority* to send but no *capability* to invent them. A failure on one side cannot
become a send on the other. This is the single most important property — it is what makes a
prompt injection a non-event rather than an outbound message.

### 2. A blast radius you can reason about
When something goes wrong you can name exactly what each side could and couldn't do. The
transport could, at worst, send an already-approved draft to the wrong thread (fixable with
the draft-bound token). The brain could, at worst, write a bad draft — which is caught in
shadow before anyone sees it. There is no "the model went rogue and messaged a customer,"
because the model has no socket.

### 3. Independent failure and upgrade
Restart the brain, swap its model, redeploy it — the WhatsApp session never drops, because
it lives in the transport. Re-pair the transport after a session expiry — no draft is lost,
because drafts live in shadow/queue. Neither side's failure cascades.

### 4. An autonomy dial you can trust
Because the guards (see `governance-loop.md`) sit *between* the two processes rather than
inside one, you can move the autonomy threshold per contact or per intent without touching
the agent's logic. Same loop, different gate. You cannot safely do that when the guard is a
prompt instruction inside the same process that holds the socket.

### 5. The wire is replaceable
The transport is a commodity — any linked-device client implements the same narrow contract
(push inbound, send approved outbound). Your investment is the brain layer and the loop, and
it survives swapping the transport entirely.

## The contract between them

Keep it as narrow as possible. Two message shapes cross the queue:

```
inbound  = { from, text, media?, timestamp, thread_id }
outbound = { to, text, draft_id, send_token }
```

The `send_token` is the whole game (see `governance-loop.md` stage ⑥): the transport refuses
to send any outbound that does not carry a valid, single-use, draft-bound token. That one
field is what turns "the brain wrote something" into "a human approved *this exact text* to
*this exact person*, once."

## When NOT to use this

If the operator is the only human in the loop — you talking to your own agent — this is
overkill. Use a transport repo directly and skip the brain/governance tiers. The split earns
its complexity only when the far end is a stranger.
