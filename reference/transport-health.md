# Transport health — the part that decides whether it survives production

> Credit: this layer was scoped by **Graeme C** in the RoboNuggets thread on the v2 scaffold.
> His point, verbatim in spirit: *"Your governance loop is perfect, it's just not running — and
> you find out when a client does, not when you do. Build a transport health-check: a heartbeat
> per number that pauses the bot the second a session degrades and pings you before the client
> notices it went quiet."* That's the line between a demo and something you can charge for.

The brain (v1) and the governance loop (v2) are the *fun 20%*. They barely change once they
work. What actually kills a WhatsApp agent in production is the **transport**: linked-device
sessions drop, tokens expire, numbers get flagged. When that happens your loop is still perfect
— it's just not running. Messages stop going out, and the first person to notice is the client,
not you.

## The fix: a per-number circuit breaker

A **heartbeat per number** probes each transport session on a cadence — is the session alive, is
the token valid, is the number unflagged? The loop consults it **before every send**:

```
inbound → context → draft → policy → [ transport healthy? ] → shadow → approve → token → send
                                            │ no
                                            ▼
                                   HOLD the draft + alert the operator
```

Two properties make it worth the small amount of code:

1. **Auto-pause beats every other gate.** If a number's transport is degraded, *every* draft to
   it is held — even an `auto_approve` one. A perfect, confident, approved reply is worthless if
   the wire is dead; holding it (drafted, waiting) is strictly better than firing it into a
   dropped session.
2. **The operator hears it first.** The heartbeat fires a single alert on the transition *into* a
   bad state — so you find out the moment the session degrades, before the silence reaches a
   client. "Pause before the client notices," not "go quiet on a client."

## In this scaffold

- [`scaffold/transport/health.py`](../scaffold/transport/health.py) — `HealthMonitor`: per-number
  state (`HEALTHY` / `DEGRADED` / `DOWN`), `heartbeat()` (alerts on the edge into a bad state),
  and `is_sendable()`.
- [`scaffold/brain/loop.py`](../scaffold/brain/loop.py) — one surgical gate: `if health is not
  None and not health.is_sendable(draft.to): hold as transport_paused`. With `health=None` the
  loop behaves exactly as v2 (backward-compatible).
- [`scaffold/run_health_demo.py`](../scaffold/run_health_demo.py) — `python run_health_demo.py`
  shows the same routine message to the same trusted contact get auto-sent, then **held** the
  moment its transport drops (operator alerted), then auto-sent again once the session re-links.

## Adapting it to a real transport

The heartbeat in the scaffold is driven by explicit `heartbeat()` calls so the demo is
deterministic. In production, run it as a periodic probe of your linked-device client and map its
signals onto the health states:

| Transport signal | Health |
|---|---|
| session alive, token valid, number clean | `HEALTHY` |
| heartbeat slow, token near expiry, soft warning | `DEGRADED` (pause + alert) |
| session dropped / device unlinked / number flagged | `DOWN` (pause + alert) |

Wire the `alert` callback to wherever the operator actually lives (a Telegram DM, a page, a
dashboard), and feed the same probe results into `heartbeat()`. The brain and governance loop
stay exactly as they are — the health-check sits in front of the wire, not inside the agent.
