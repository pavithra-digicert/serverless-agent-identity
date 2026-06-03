# AZURE PRODUCTION - Azure Managed Identity is the trust anchor
# Equivalent role to SPIRE Server in container workloads
# Requires: Managed Identity enabled on the Azure Function
# Requires env vars: AZURE_TENANT_ID, AZURE_RESOURCE (optional)

from __future__ import annotations

import os

import jwt
from jwt import PyJWKClient
from azure.identity import ManagedIdentityCredential
from dotenv import load_dotenv

load_dotenv()

AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
AZURE_RESOURCE: str = os.getenv(
    "AZURE_RESOURCE", "https://management.azure.com/.default"
)

# Cached JWKS client - keys are fetched once and reused across invocations.
# PyJWKClient also handles key rotation automatically when a kid is not found.
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(get_trust_bundle())
    return _jwks_client


def get_managed_identity_token(resource: str | None = None) -> str:
    """Obtain a token from Azure Managed Identity."""
    target = resource or AZURE_RESOURCE
    credential = ManagedIdentityCredential()
    token = credential.get_token(target)
    return token.token


def verify_svid(token: str) -> dict:
    """Verify an Azure Managed Identity JWT token using the Azure AD JWKS endpoint."""
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "reason": "Token has expired"}
    except jwt.InvalidTokenError as exc:
        return {"valid": False, "reason": str(exc)}
    except Exception as exc:
        return {"valid": False, "reason": f"JWKS verification failed: {exc}"}


def get_trust_bundle() -> str:
    """Return the Azure AD JWKS endpoint URL for this tenant."""
    if not AZURE_TENANT_ID:
        raise EnvironmentError("AZURE_TENANT_ID env var is not set")
    return f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/keys"
