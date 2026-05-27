from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


_ENVIRONMENT: str = os.getenv("ENVIRONMENT", "").strip().lower()

if not _ENVIRONMENT:
    print(
        "[sdk.bootstrap] WARNING: ENVIRONMENT env var is not set — "
        "defaulting to 'local'. Set ENVIRONMENT=local or ENVIRONMENT=azure explicitly."
    )
    _ENVIRONMENT = "local"

if _ENVIRONMENT == "azure":
    from sdk.azure.spire_agent import bootstrap, verify_token
elif _ENVIRONMENT == "local":
    from sdk.local.spire_agent import bootstrap, verify_token
else:
    print(
        f"[sdk.bootstrap] WARNING: Unknown ENVIRONMENT={_ENVIRONMENT!r} — "
        "defaulting to 'local'."
    )
    from sdk.local.spire_agent import bootstrap, verify_token

__all__ = ["bootstrap", "verify_token"]
