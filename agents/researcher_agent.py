from __future__ import annotations

from sdk.bootstrap import bootstrap
from sdk.identity import AgentIdentity


def run(query: str) -> tuple[str, AgentIdentity]:
    """Bootstrap identity and return a stub result. Agent logic goes here later."""
    identity = bootstrap("researcher-agent")
    print(f"[researcher-agent] Identity bootstrapped:\n  {identity!r}\n")

    # Stub: no LLM or tool logic yet - replaced with real agent logic later.
    result = f"[STUB] Hardcoded result for query: {query!r}"
    return result, identity
