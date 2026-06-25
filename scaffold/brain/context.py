"""Stage 2 — context assembly. Gather, do not invent.

This is where a reply becomes *business-correct* instead of merely fluent. In production
this reads your real contact-memory store and enrichment sources; here it's a JSON file.
The point of the stage is the same either way: assemble BEFORE drafting, so the model
grounds in real relationship history instead of hallucinating it.
"""
import json


def assemble_context(inbound, contacts_path):
    with open(contacts_path) as f:
        contacts = json.load(f)

    profile = contacts.get(inbound.sender, {})
    return {
        "known": bool(profile),                              # have we met this person?
        "name": profile.get("name", "there"),
        "relationship": profile.get("relationship", "unknown / first contact"),
        "history": profile.get("history", []),               # prior commitments, threads
        "facts": profile.get("facts", {}),                   # domain enrichment
    }
