# LOCAL ONLY — simulates SPIRE Server for dev/experiment
# In production this role is played by Azure Managed Identity
# Never use this in production

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from dotenv import load_dotenv

load_dotenv()

TRUST_DOMAIN: str = os.getenv("TRUST_DOMAIN", "experiment.local")


_private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)
_public_key = _private_key.public_key()


def sign_svid(
    spiffe_id: str,
    agent_name: str,
    instance_id: str,
    trust_domain: str,
    ttl_seconds: int,
) -> tuple[str, datetime, datetime]:
   
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)

    payload = {
        "sub": spiffe_id,
        "iss": trust_domain,
        "aud": f"spiffe://{trust_domain}",
        "iat": now,
        "exp": expires_at,
        "agent_name": agent_name,
        "instance_id": instance_id,
        "trust_domain": trust_domain,
    }

    token: str = jwt.encode(payload, _private_key, algorithm="RS256")
    return token, now, expires_at


def verify_svid(token: str) -> dict:
   
    try:
        payload = jwt.decode(
            token,
            _public_key,
            algorithms=["RS256"],
            audience=f"spiffe://{TRUST_DOMAIN}",
        )
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "reason": "Token has expired"}
    except jwt.InvalidAudienceError:
        return {"valid": False, "reason": "Invalid audience"}
    except jwt.InvalidTokenError as exc:
        return {"valid": False, "reason": str(exc)}


def get_trust_bundle():
    return _public_key
