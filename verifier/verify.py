from __future__ import annotations

from sdk.bootstrap import verify_token


def verify(token: str) -> None:
    """Verify an agent identity token and print the outcome."""
    result = verify_token(token)

    if result["valid"]:
        payload = result["payload"]
        print("Status     : VERIFIED")
        print(f"  SPIFFE ID  : {payload['sub']}")
        print(f"  Agent Name : {payload['agent_name']}")
        print(f"  Instance ID: {payload['instance_id']}")
    else:
        print(f"Status     : REJECTED")
        print(f"  Reason     : {result['reason']}")
