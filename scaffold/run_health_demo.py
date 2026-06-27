#!/usr/bin/env python3
"""v3 demo — the transport health-check. Runs with NO API key, NO WhatsApp pairing.

    python run_health_demo.py

Shows the part Graeme C said decides whether the agent survives production: a heartbeat per
number that auto-pauses the bot the second the transport degrades and pings the operator BEFORE
the client notices the silence. Same brain + governance loop as v2 — we just add a circuit
breaker in front of the wire.

Watch the same routine message to the same trusted contact get auto-sent, then HELD the moment
its transport drops (operator alerted), then auto-sent again once the session re-links.
"""
import os

from brain.seam import Inbound, Queue
from brain.shadow import Shadow
from brain.tokens import TokenVault
from brain.loop import handle
from transport.mock import MockTransport
from transport.health import HealthMonitor, Health

HERE = os.path.dirname(os.path.abspath(__file__))
CONTACTS = os.path.join(HERE, "sample_data", "contacts.json")
INBOX = os.path.join(HERE, "sample_data", "inbox.json")  # unused here; MockTransport just sends

DANA = "+15550000001"   # known supplier in contacts.json → routine asks auto-approve


def operator_alert(number, health, reason):
    print(f"  🚨 OPERATOR ALERT — {number} is {health.value.upper()}: {reason}")
    print(f"     bot paused for this number. The client hasn't noticed the silence yet.")


def msg(text):
    return Inbound(sender=DANA, text=text, thread_id="t1", timestamp="2026-06-27T20:00:00Z")


def run(inbound, *, shadow, tokens, outbound, health, transport):
    out = handle(inbound, contacts_path=CONTACTS, shadow=shadow, tokens=tokens,
                 outbound_queue=outbound, health=health)
    status = health.status(out.to).value
    print(f"  inbound {out.inbound_text!r}  → lane: {out.lane}  (transport: {status})")
    for ob in outbound.drain():
        transport.send(ob, tokens)
    if not out.sent:
        print(f"     ⤷ held, not sent (drafted and waiting — nothing went quiet on the client)")


def main():
    transport = MockTransport(INBOX)
    shadow, tokens, outbound = Shadow(), TokenVault(), Queue()
    health = HealthMonitor(alert=operator_alert)

    print("\nwa-brain-pattern v3 demo · transport health-check\n" + "=" * 70)

    print("\n1) Transport HEALTHY — heartbeat green, session linked:")
    health.heartbeat(DANA, Health.HEALTHY)
    run(msg("Hey, can you confirm Thursday?"), shadow=shadow, tokens=tokens,
        outbound=outbound, health=health, transport=transport)

    print("\n2) Heartbeat FAILS — the linked-device session just dropped:")
    health.heartbeat(DANA, Health.DOWN, reason="WhatsApp session dropped (device unlinked)")
    run(msg("Did you see my last message?"), shadow=shadow, tokens=tokens,
        outbound=outbound, health=health, transport=transport)

    print("\n3) Heartbeat RECOVERS — session re-linked, number clean:")
    health.heartbeat(DANA, Health.HEALTHY)
    run(msg("Still on for Thursday?"), shadow=shadow, tokens=tokens,
        outbound=outbound, health=health, transport=transport)

    print("\n" + "=" * 70)
    held = shadow.pending("transport_paused")
    print(f"sent while healthy: {len(transport.sent)}   held during the outage: {len(held)}")
    print("The governance loop never changed. The transport health-check is what kept a dead")
    print("session from going silent on a client — and told the operator first.\n")


if __name__ == "__main__":
    main()
