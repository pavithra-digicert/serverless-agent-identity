from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class AgentIdentity:
    spiffe_id: str
    agent_name: str
    trust_domain: str
    token: str
    expires_at: datetime
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    instance_id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def as_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def __repr__(self) -> str:
        status = "EXPIRED" if self.is_expired else "VALID"
        return (
            f"AgentIdentity("
            f"spiffe_id={self.spiffe_id!r}, "
            f"instance_id={self.instance_id!r}, "
            f"status={status!r}, "
            f"expires_at={self.expires_at.isoformat()!r}"
            f")"
        )
