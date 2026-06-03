from __future__ import annotations

from agents.researcher_agent import run
from verifier.verify import verify


def main() -> None:
    print("  Serverless Agent Identity - Experiment Run")

    result, identity = run("Some AI agent WF")

    print(f"Agent result : {result}\n")

    print("  Verifying agent identity token...")
    verify(identity.token)


if __name__ == "__main__":
    main()
