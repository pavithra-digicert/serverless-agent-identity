# LOCAL ONLY - simulates SPIRE Agent sidecar for dev/experiment
# In production this role is played by sdk/azure/spire_agent.py

from __future__ import annotations

from uuid import uuid4

from sdk.identity import AgentIdentity
from sdk.local.spire_server import TRUST_DOMAIN, sign_svid, verify_svid


def bootstrap(agent_name: str, ttl_seconds: int = 3600) -> AgentIdentity:
    instance_id = str(uuid4())
    spiffe_id = f"spiffe://{TRUST_DOMAIN}/agent/{agent_name}"

    token, issued_at, expires_at = sign_svid(
        spiffe_id=spiffe_id,
        agent_name=agent_name,
        instance_id=instance_id,
        trust_domain=TRUST_DOMAIN,
        ttl_seconds=ttl_seconds,
    )

    return AgentIdentity(
        spiffe_id=spiffe_id,
        agent_name=agent_name,
        trust_domain=TRUST_DOMAIN,
        token=token,
        expires_at=expires_at,
        issued_at=issued_at,
        instance_id=instance_id,
    )


def verify_token(token: str) -> dict:
    return verify_svid(token)
