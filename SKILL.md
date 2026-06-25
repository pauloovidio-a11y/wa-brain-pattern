---
name: wa-brain-pattern
description: >-
  Reference architecture for running an AUTONOMOUS WhatsApp agent on Claude Code —
  one that answers inbound messages from third parties (clients, suppliers, leads) on a
  business line, safely. Use when someone wants Claude Code to handle stranger-facing
  WhatsApp, not just "chat with my own agent from my phone." Teaches the two-tier
  brain/transport split and the draft → shadow → approve → token-gate → send governance
  loop. Triggers on "autonomous whatsapp", "whatsapp agent answer customers",
  "claude code whatsapp business", "wa-brain", "brain transport pattern".
---

# wa-brain-pattern — autonomous WhatsApp on Claude Code

This is primarily a **documentation skill**: it teaches Claude Code a *topology* and helps the
user adapt it onto whatever WhatsApp transport they already use. It does not install a bot or
open a socket. A **runnable reference scaffold** ships alongside it (`scaffold/`) so the user can
see the pattern work end-to-end before building.

Read this whole file before advising. The companion deep-dives live in `reference/`; the working
implementation lives in `scaffold/` (run it with `python scaffold/run_demo.py` — no API key, no
WhatsApp pairing).

---

## What problem this solves (and what it does NOT)

There are ~10 public repos for connecting Claude Code to WhatsApp. **They all solve the
same thing:** *you* talking to *your own* Claude Code from your phone — a remote terminal,
an MCP tool, or a phone-based approval surface. The operator is the only human in the loop.

This pattern solves the **inverse and harder** problem:

> An **autonomous agent answering inbound from strangers** — real clients, suppliers, and
> leads messaging a business line — where the model's words reach a real person only after
> clearing explicit safety gates.

If the user just wants to **chat with their own Claude Code over WhatsApp**, this is the
wrong skill. Point them at the transport repos (see "Transport tier" below) and stop —
do not over-build.

---

## The core idea: split the brain from the transport

The mistake almost everyone makes is fusing the model and the wire into one process. That
is fine when you are talking to yourself. It is a liability the moment the other party is
a stranger.

**Two tiers, sharing nothing but a queue:**

```
        THE BRAIN                         THE TRANSPORT
   Claude Code · Opus                 Linked-device WA client
   ─────────────────────             ─────────────────────────
   • reads context + memory          • Baileys / WhatsApp Web (QR pair)
   • composes the reply              • receives inbound → emits to queue
   • decides intent & routing        • sends APPROVED drafts verbatim
   • NEVER touches the socket        • NEVER composes a single word
              │                                   │
              └────────────  shared queue  ───────┘
                         (the only contract)
```

- The **brain** is the only thing that *thinks*. It has no network access to WhatsApp.
- The **transport** is the only thing on the *wire*. It has no judgment and no creativity.
- **Capability is split from authority.** A prompt-injection in an inbound message cannot
  make the brain send (it has no socket). The transport cannot invent a promise to a
  customer (it has no model). Neither failure cascades into the other.

Full rationale: `reference/topology.md`.

---

## The governance loop

Every inbound message walks this path. Model output does not reach a human until it has
cleared **shadow**, won an **approval**, and consumed a **single-use outbound token**.

```
 ① inbound        ② context assembly      ③ Opus draft       ④ shadow
 stranger DMs  →  contact memory +      →  brain composes  →  staged,
 the business     profile enrichment       the reply           not sent
 line                                                              │
                                                                   ▼
 ⑦ send       ←   ⑥ outbound token   ←   ⑤ approval bridge
 transport        gate (one-shot,        operator approves /
 emits verbatim   bound to this draft)   edits / vetoes
```

**The guards are stages ④–⑥.** Strip any one of them and you are back to "fire raw LLM
output at a customer." Keep all three and you can dial autonomy up or down *per contact or
per intent* — full-auto for low-stakes, shadow-only for high-stakes — without rewriting the
agent. The loop stays the same; only the gate threshold moves.

Full breakdown of each stage, including failure modes: `reference/governance-loop.md`.

---

## How to help the user adopt this

When this skill fires, do NOT start writing a WhatsApp client. Work through these steps
with the user, in order:

1. **Confirm the use case.** Ask: "Is this answering *strangers* on a business line, or
   talking to your *own* agent?" If the latter → recommend a transport repo and stop.

2. **Pick the transport tier (don't build it).** The wire is a commodity — any
   linked-device client works. The community reference is
   **[Rich627/whatsapp-claude-plugin](https://github.com/Rich627/whatsapp-claude-plugin)**
   (Baileys, no Business API, no keys). The user runs that as the transport and builds the
   brain on top. Other options: `lharries/whatsapp-mcp`, `jlucaso1/whatsapp-mcp-ts`.

3. **Design the seam.** The brain and transport must share *only* a queue / outbox. Help
   the user define the two message shapes that cross it:
   - inbound: `{from, text, media?, timestamp, thread_id}`
   - outbound: `{to, text, draft_id, send_token}`  ← note the token (stage ⑥)

4. **Stand up the brain layer** as a Claude Code process that consumes inbound, runs
   context assembly, drafts, and writes to shadow. Start from the runnable `scaffold/`
   (a working brain + loop over a mock transport) and/or the interfaces in
   `reference/adapt.md`. The user adapts these for their domain.

5. **Wire the three guards.** Shadow (a holding store), an approval bridge (Telegram DM,
   a CLI, a web button — operator's choice), and a one-shot outbound token the transport
   verifies before sending. This is the part with real value; spend the time here.

6. **Start in shadow-only.** Every draft staged, nothing auto-sent, operator approves all.
   Graduate specific contacts/intents to auto-send only after the drafts are consistently
   good. Never ship straight to full-auto on a stranger-facing line.

---

## Hard rules (read before advising)

- **Never auto-send on first build.** Shadow-only until drafts are proven. This is not
  optional for stranger-facing autonomy.
- **The brain never gets a WhatsApp socket.** If you find yourself giving the brain process
  send capability, you have collapsed the pattern. Route through the queue + token.
- **The transport never composes.** It carries bytes. If it is doing string templating of
  replies, that logic belongs in the brain.
- **Don't rebuild the wire.** Transport is solved and commoditized. Build the brain +
  governance loop; that is the differentiated work.
- **Keep the outbound token single-use and draft-bound.** It is what makes "approved" mean
  *this exact text to this exact person, once*. The scaffold's `brain/tokens.py` shows the
  verify-and-burn primitive; `transport/mock.py` shows the transport refusing a tokenless send.

---

## Why this is worth the extra structure

`reference/topology.md` covers it in full, but the short version: because the guards are
*structural* rather than vibes, you get an autonomy dial you can actually trust. You can
grant the agent real authority over a business line — and reason precisely about the blast
radius when something goes wrong — because the thing that thinks and the thing that sends
are different processes that agree on one narrow contract.

The connection is commoditized. **The orchestration is the IP.**

---

*Visual one-pager: `docs/index.html` (also hosted via GitHub Pages — see the repo README).*
*Shared with the RoboNuggets community.*
