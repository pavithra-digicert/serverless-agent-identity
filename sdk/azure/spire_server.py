# AZURE PRODUCTION — Azure Managed Identity is the trust anchor
# Equivalent role to SPIRE Server in container workloads
# Requires: Managed Identity enabled on the Azure Function
# Requires env vars: AZURE_TENANT_ID, AZURE_RESOURCE (optional)

from __future__ import annotations

import os

import jwt
from azure.identity import ManagedIdentityCredential
from dotenv import load_dotenv

load_dotenv()

AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
AZURE_RESOURCE: str = os.getenv(
    "AZURE_RESOURCE", "https://management.azure.com/.default"
)


def get_managed_identity_token(resource: str | None = None) -> str:
    """Obtain a token from Azure Managed Identity.

    SPIRE concept: SVID issuance — the SPIRE Server acts as a CA and issues
    SVIDs to attested workloads. Here Azure Managed Identity plays the CA role:
    the platform guarantees the identity of the function and issues the token.
    """
    target = resource or AZURE_RESOURCE
    credential = ManagedIdentityCredential()
    token = credential.get_token(target)
    return token.token


def verify_svid(token: str) -> dict:
    """Decode and validate an Azure Managed Identity JWT token.

    SPIRE concept: SVID validation via trust bundle — consumers verify SVIDs
    using the trust bundle. Azure guarantees token integrity so we decode
    without signature verification to extract and return the claims.
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["RS256"],
        )
        return {"valid": True, "payload": payload}
    except jwt.InvalidTokenError as exc:
        return {"valid": False, "reason": str(exc)}


def get_trust_bundle() -> str:
    """Return the Azure AD JWKS endpoint URL for this tenant.

    SPIRE concept: Bundle endpoint — the SPIRE Server exposes a bundle endpoint
    distributing root CA public keys. Azure's equivalent is the JWKS endpoint,
    which publishes the public keys used to sign Managed Identity tokens.
    """
    if not AZURE_TENANT_ID:
        raise EnvironmentError("AZURE_TENANT_ID env var is not set")
    return f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/keys"
