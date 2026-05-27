from __future__ import annotations

from agents.researcher_agent import run
from verifier.verify import verify


def main() -> None:
    print("=" * 52)
    print("  Serverless Agent Identity — Experiment Run")
    print("=" * 52)

    result, identity = run("Latest AI agent frameworks")

    print(f"Agent result : {result}\n")

    print("=" * 52)
    print("  Verifying agent identity token...")
    print("=" * 52)
    verify(identity.token)


if __name__ == "__main__":
    main()
