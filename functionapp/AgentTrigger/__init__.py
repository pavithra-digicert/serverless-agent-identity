# To run locally:
#   cd functionapp
#   func start
#   curl "http://localhost:7071/api/AgentTrigger?task=AI+agent+frameworks"
#
# To switch to Azure Managed Identity:
#   set ENVIRONMENT=azure in Azure app settings
#   no code changes needed

import sys
import os

_HERE = os.path.dirname(__file__)

# Add locally installed packages (pip install --target) so the Functions
# runtime picks them up without needing a global pip install.
sys.path.insert(0, os.path.join(_HERE, "..", ".python_packages", "lib", "site-packages"))

# Local dev: sdk/, agents/, verifier/ live two levels up (repo root).
# Azure deployment: those folders are copied into functionapp/ before publish,
# so they are one level up (wwwroot root). Add both; Python uses the first match.
sys.path.insert(0, os.path.join(_HERE, ".."))       # Azure: wwwroot/
sys.path.insert(0, os.path.join(_HERE, "..", ".."))  # Local: repo root

import json
import logging

import azure.functions as func

from agents.researcher_agent import run
from verifier.verify import verify_token


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("AgentTrigger: processing request")

    try:
        # Read "task" from query string, then fall back to JSON body.
        task: str | None = req.params.get("task")
        if not task:
            try:
                body = req.get_json()
                task = body.get("task")
            except (ValueError, AttributeError):
                pass

        if not task:
            task = "default research task"

        # Run the stub agent — no changes to researcher_agent.py.
        result, identity = run(task)

        # Verify the agent's identity token from inside the function itself.
        verification_result = verify_token(identity.token)
        verification: dict = {"valid": verification_result["valid"]}
        if not verification_result["valid"]:
            verification["reason"] = verification_result.get("reason", "unknown")

        response_body = {
            "task": task,
            "answer": result,
            "identity": {
                "spiffe_id": identity.spiffe_id,
                "agent_name": identity.agent_name,
                "instance_id": identity.instance_id,
                "expires_at": identity.expires_at.isoformat(),
                "status": "EXPIRED" if identity.is_expired else "VALID",
            },
            "verification": verification,
            "environment": os.getenv("ENVIRONMENT", "local"),
        }

        return func.HttpResponse(
            body=json.dumps(response_body, indent=2),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as exc:
        logging.exception("AgentTrigger: unhandled exception")
        return func.HttpResponse(
            body=json.dumps({"error": str(exc)}),
            status_code=500,
            mimetype="application/json",
        )
