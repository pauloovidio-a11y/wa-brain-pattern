# The governance loop — stage by stage

Every inbound message walks this path. The point of the loop is that model output does not
reach a real person until it has cleared three guards: **shadow**, **approval**, and a
**single-use outbound token**.

```
 ① inbound  →  ② context  →  ③ draft  →  ④ shadow  →  ⑤ approval  →  ⑥ token gate  →  ⑦ send
                                          └──────────── the guards ────────────┘
```

---

## ① Inbound
A stranger messages the business line. The **transport** receives it (it owns the WhatsApp
session) and pushes a normalized envelope onto the queue:

```
{ from, text, media?, timestamp, thread_id }
```

The transport does nothing intelligent here — no parsing of intent, no templating. It
normalizes and forwards.

**Failure mode to avoid:** putting any "if message contains X, reply Y" logic in the
transport. That is brain work. The transport stays dumb.

---

## ② Context assembly
The **brain** pulls the inbound envelope and assembles the context the draft will be grounded
in. Two ingredients matter most:

- **Contact memory** — what you already know about this person and thread (prior messages,
  commitments made, their status, open threads). Never re-ask something the contact already
  told you.
- **Profile enrichment** — any structured facts the domain needs (account type, entitlements,
  prior orders, relationship stage). Pulled from your own store, not invented.

This stage is where a reply becomes *business-correct* instead of merely fluent. It is worth
investing in; a great model with no context still writes generic, wrong answers.

**Failure mode:** drafting before assembling. A model with empty context will hallucinate
relationship history. Assemble first, draft second.

---

## ③ Opus draft
The brain composes the candidate reply (or proposal, or relay) using the assembled context.
This is the *only* creative step in the whole loop. The output is a **draft** — a proposed
message, not a sent one.

**Failure mode:** letting the draft step also send. It must hand off to shadow. If your draft
function can reach the wire, the pattern is already broken.

---

## ④ Shadow  ·  GUARD 1
The draft is written to a **holding store** — staged, visible to the operator, *not sent*. In
shadow, a draft is a candidate the system is *considering*, nothing more.

Shadow is what lets you run the whole pipeline in "observe" mode from day one: every inbound
gets a full draft, you watch the quality accumulate, and nothing has gone out. You graduate
contacts/intents out of shadow-only as the drafts prove themselves.

**Failure mode:** skipping shadow "because the drafts look good." Shadow-first is how you
*learn* they're good without risking a real send. Never ship straight past it on a
stranger-facing line.

---

## ⑤ Approval bridge  ·  GUARD 2
The operator gets the staged draft and decides: **approve / edit / veto.** The bridge can be
anything that reaches the operator — a Telegram DM, a CLI prompt, a web button, a message to
their own number. The transport is irrelevant here; this is operator ↔ system, not
agent ↔ stranger.

- **Approve** → the draft proceeds to the token gate.
- **Edit** → operator adjusts the text, then approves the edited version.
- **Veto** → the draft is dropped; optionally feed the reason back into context so the brain
  learns.

For trusted, low-stakes contacts/intents you can make approval *implicit* (auto-approve after
a delay, or by policy) — but that is a per-lane decision you make deliberately, not a default.

**Failure mode:** an approval surface the operator doesn't actually watch. A guard nobody
reads is not a guard. Put it where the operator already lives.

---

## ⑥ Outbound token gate  ·  GUARD 3
On approval, the system issues a **single-use, draft-bound send token** and attaches it to the
outbound envelope:

```
{ to, text, draft_id, send_token }
```

The transport **refuses to send** any outbound lacking a valid token, and each token is
valid for exactly one send of exactly one draft. This is what makes "approved" precise:
*this exact text, to this exact person, once.* It also closes the replay/duplication hole —
a token can't be reused to re-send.

**Failure mode:** a global "sending is enabled" flag instead of per-draft tokens. That gates
*whether* the system can send, not *what* it sends — so an approved draft and an unapproved
one are indistinguishable at the wire. Bind the token to the draft.

---

## ⑦ Send
The transport verifies the token and emits the approved text **verbatim** to the recipient.
No last-minute templating, no re-generation. What the operator approved is what goes out.

---

## The whole point
Stages ④–⑥ are the guards. Each closes a specific hole:

| Guard | Closes |
|-------|--------|
| ④ Shadow | "raw model output reached a customer before anyone saw it" |
| ⑤ Approval | "nobody chose to send this" |
| ⑥ Token gate | "an unapproved/duplicate message went out on the wire" |

Keep all three and you can grant real autonomy over a stranger-facing line while still being
able to reason precisely about what can go wrong. Remove any one and you are back to firing
raw LLM output at a real person.
