# AZURE PRODUCTION — equivalent to SPIRE Agent sidecar
# In containers: SPIRE Agent runs as a sidecar
# In Azure Functions: this SDK layer replaces the sidecar

from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import jwt
from sdk.azure.spire_server import AZURE_TENANT_ID, get_managed_identity_token, verify_svid
from sdk.identity import AgentIdentity


def bootstrap(agent_name: str, ttl_seconds: int = 3600) -> AgentIdentity:
    """Attest the workload and deliver an Azure MI token as an AgentIdentity.

    SPIRE concept: Workload API — the SPIRE Agent attests workloads and delivers
    their SVID. Here the Azure platform performs attestation via Managed Identity;
    this function fetches the resulting token and wraps it in an AgentIdentity.

    ttl_seconds is kept for API compatibility; actual expiry is taken from the
    Azure token's 'exp' claim — the platform controls the token lifetime.
    """
    raw_token = get_managed_identity_token()

    # Decode without verification — Azure guarantees the token's authenticity.
    claims = jwt.decode(
        raw_token,
        options={"verify_signature": False},
        algorithms=["RS256"],
    )

    spiffe_id = f"spiffe://{AZURE_TENANT_ID}/agent/{agent_name}"
    issued_at = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)

    # WEBSITE_INSTANCE_ID is set automatically by Azure Functions per instance.
    instance_id = os.getenv("WEBSITE_INSTANCE_ID") or str(uuid4())

    return AgentIdentity(
        spiffe_id=spiffe_id,
        agent_name=agent_name,
        trust_domain=AZURE_TENANT_ID,
        token=raw_token,
        expires_at=expires_at,
        issued_at=issued_at,
        instance_id=instance_id,
    )


def verify_token(token: str) -> dict:
    """Validate an Azure MI JWT-SVID by delegating to the server's trust bundle.

    SPIRE concept: Workload API validation — the SPIRE Agent provides a local
    verification path. Here we delegate to spire_server; this module owns no
    key material.
    """
    return verify_svid(token)
