# wa-brain-pattern

**A reference architecture for running an _autonomous_ WhatsApp agent on Claude Code — one
that answers inbound from strangers (clients, suppliers, leads) on a business line, safely.**

> 📄 **[Read the one-page visual →](https://pauloovidio-a11y.github.io/wa-brain-pattern/)**
> (diagrams + the governance loop)

---

## The gap this fills

There are ~10 public repos for connecting Claude Code to WhatsApp. They're good — and they
all solve the **same** thing: *you* talking to *your own* agent from your phone (a remote
terminal, an MCP tool, or a phone-based approval surface). The operator is the only human
in the loop.

Nobody has packaged the **inverse and harder** problem:

> an **autonomous agent answering strangers** on a business line, where the model's words
> reach a real person only after clearing explicit safety gates.

This repo is the topology that does it.

## The idea in 30 seconds

Stop fusing the model and the wire. **Split them:**

```
        THE BRAIN                         THE TRANSPORT
   Claude Code · Opus                 Linked-device WA client
   drafts · remembers · reasons       carries bytes · stays dumb
   NEVER touches the socket           NEVER composes a word
              │                                   │
              └───────────  shared queue  ────────┘
```

Between them runs a governance loop so the model never fires raw output at a customer:

```
 inbound → context assembly → Opus draft → SHADOW → approval → token gate → send
                                            └──────── the guards ────────┘
```

- **Capability is split from authority** — a prompt-injection in an inbound message can't
  make the brain send (it has no socket); the transport can't invent a promise (it has no
  model).
- **The guards are structural, not vibes** — so you get an autonomy dial you can actually
  trust, tunable per contact or per intent.
- **The connection is commoditized. The orchestration is the IP.**

## What's in here

| File | What it is |
|------|-----------|
| [`SKILL.md`](SKILL.md) | The installable Claude Code skill — teaches the pattern and walks you through adopting it |
| [`reference/topology.md`](reference/topology.md) | Why split the brain from the transport (full rationale) |
| [`reference/governance-loop.md`](reference/governance-loop.md) | The 7-stage loop, stage by stage, with failure modes |
| [`reference/adapt.md`](reference/adapt.md) | Stub interfaces — wiring the pattern onto your transport |
| [`docs/index.html`](docs/index.html) | The visual one-pager (also hosted via GitHub Pages) |

This is a **documentation skill** — it installs *understanding*, not a running bot. It does
not open a WhatsApp socket or ship a transport. You bring the transport; this teaches the
brain + governance layer that sits on top.

## Install (Claude Code)

```
I'm giving you a skill called wa-brain-pattern.

git clone https://github.com/pauloovidio-a11y/wa-brain-pattern ~/.claude/skills/wa-brain-pattern

Read the SKILL.md, recommend how this pattern applies to my setup in plain language,
and ask me a few questions about my use case before we build anything.
```

Claude Code will read the skill, figure out whether you actually need the autonomous pattern
(or just a transport repo), and help you adapt it.

## The transport tier (bring your own)

The wire is a commodity — don't rebuild it. Run an existing linked-device client and build
the brain on top:

- **[Rich627/whatsapp-claude-plugin](https://github.com/Rich627/whatsapp-claude-plugin)** —
  community reference. Baileys, no Business API, no API keys, no Docker. This is also the one
  to use if you _only_ want to chat with your own Claude Code over WhatsApp.
- [`lharries/whatsapp-mcp`](https://github.com/lharries/whatsapp-mcp) ·
  [`jlucaso1/whatsapp-mcp-ts`](https://github.com/jlucaso1/whatsapp-mcp-ts) — MCP alternatives.

## Credits

Shared with the [RoboNuggets](https://www.skool.com/robonuggets) community. The transport-tier
reference is [Rich627/whatsapp-claude-plugin](https://github.com/Rich627/whatsapp-claude-plugin).

## License

MIT — see [`LICENSE`](LICENSE).
