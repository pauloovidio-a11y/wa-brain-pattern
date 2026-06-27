# wa-brain-pattern — working scaffold

A small, **runnable** reference implementation of the brain/transport pattern and its
governance loop. It runs end-to-end with **no WhatsApp pairing and no API key** — a mock
transport replays a scripted inbox and a mock brain drafts replies, so you can watch the
whole loop work before wiring anything real.

```bash
cd scaffold
python run_demo.py            # run the loop over a scripted inbox
python run_demo.py --review   # then interactively approve/edit/veto the held drafts
python run_health_demo.py     # v3: the transport health-check (heartbeat → auto-pause → alert)
```

Optional — use the real Opus brain for drafting:

```bash
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY=sk-ant-...
python run_demo.py
```

## What the demo shows

```
INBOUND                                           CONF  LANE
----------------------------------------------------------------------
Hey, can you confirm you got my note about Th…    0.88  ✅ auto
hi                                                0.40  🕓 shadow      ← not confident → held
Quick one — are you free Thursday afternoon t…    0.88  ✅ auto
Also, can you send the invoice for last month…    0.55  🔒 operator    ← sensitive → held

reached the wire: 2   held by guards: 2
```

Every inbound is drafted by the brain and routed by `policy()` into a lane. Only the
`auto_approve` lane mints a token and reaches the (mock) wire; the guarded lanes stay in
shadow for a human. The demo ends by forging a tokenless send to show the transport **refuse**
it — proof that capability (drafting) is split from authority (sending).

## Layout

```
scaffold/
├── run_demo.py            # entry point — wires brain + mock transport, runs the loop
├── brain/                 # the BRAIN tier — reasons, drafts, never touches the socket
│   ├── seam.py            #   the two envelopes (Inbound, Outbound) + the queue between tiers
│   ├── context.py         #   ② assemble context (contact memory + enrichment)
│   ├── draft.py           #   ③ compose the draft (real Opus call, with mock fallback)
│   ├── policy.py          #   the autonomy dial — lanes incl. the confidence threshold
│   ├── shadow.py          #   ④ GUARD 1 — staged, not sent
│   ├── approval.py        #   ⑤ GUARD 2 — operator approve / edit / veto
│   ├── tokens.py          #   ⑥ GUARD 3 — single-use, draft-bound send token
│   └── loop.py            #   the loop, wired: inbound → … → token → send
├── transport/             # the TRANSPORT tier — carries bytes, stays dumb
│   ├── base.py            #   the interface a real linked-device client implements
│   ├── mock.py            #   a scripted stand-in; verifies the token before "sending"
│   └── health.py          #   v3: per-number heartbeat circuit breaker (auto-pause + alert)
├── run_health_demo.py     # v3 demo — heartbeat → degrade → auto-pause → operator alert → recover
└── sample_data/           # scripted contacts + inbox for the demo
```

## v3 — transport health-check

`run_health_demo.py` adds the layer that decides whether the agent survives a real linked-device
client: a **heartbeat per number** that auto-pauses the bot the moment its transport degrades
(session dropped, token expired, number flagged) and alerts the operator *before* the client
notices the silence. The brain and governance loop are unchanged — the health-check is a circuit
breaker that sits in front of the wire. A degraded number holds **every** draft, even an
auto-approve one (a confident reply into a dead session is worthless). Rationale + adapter notes:
[`../reference/transport-health.md`](../reference/transport-health.md). Credit: scoped by Graeme C
in the RoboNuggets thread.

## Swapping in a real transport

`transport/base.py` is the whole contract. Implement `receive()` (pull inbound off the wire →
`Inbound` envelopes) and `send(outbound, tokens)` (verify-and-burn the token, then send
`outbound.text` verbatim) on top of any linked-device client — the community reference is
**[Rich627/whatsapp-claude-plugin](https://github.com/Rich627/whatsapp-claude-plugin)** (Baileys,
no Business API, no keys). The entire `brain/` tier is unchanged when you do — that's the point.

> This is a **reference scaffold**, not a production system. It keeps state in memory, uses a
> CLI approval bridge, and ships a mock transport. Treat it as the skeleton to build on, and
> read [`../reference/`](../reference/) for the rationale behind each guard.
