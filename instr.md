I am building a SPIRE-equivalent identity layer for serverless AI agents on Azure Functions.
The concept: every agent gets a cryptographic identity (like a SPIFFE SVID) when it bootstraps,
instead of a sidecar handling it like SPIRE does for containers.

Create the following project structure:

agent-identity-experiment/
|- sdk/
│   |- __init__.py
│   |- identity.py
│   |- bootstrap.py
|- agents/
│   |- researcher_agent.py
|- verifier/
│   |- verify.py
|- main.py
|- requirements.txt

sdk/identity.py

Create an AgentIdentity dataclass with these fields:
- spiffe_id: str        → format: spiffe://<trust_domain>/agent/<agent_name>
- agent_name: str
- trust_domain: str
- token: str            → signed JWT
- expires_at: datetime
- issued_at: datetime   → defaults to utcnow
- instance_id: str      → defaults to a new uuid4

Add:
- is_expired property   → True if current time >= expires_at
- as_header() method    → returns {"Authorization": "Bearer <token>"}
- __repr__              → shows spiffe_id, instance_id, status, expires_at


sdk/bootstrap.py

This is the SPIRE Agent equivalent. It:
- Generates an RSA 2048 key pair at module level (local/dev mode)
- Has a bootstrap(agent_name, ttl_seconds=3600) function that:
    - Builds a SPIFFE ID: spiffe://<TRUST_DOMAIN>/agent/<agent_name>
    - Mints a signed RS256 JWT with claims:
        sub, iss, aud, iat, exp, agent_name, instance_id, trust_domain
    - Returns an AgentIdentity object
- Has a verify_token(token) function that:
    - Verifies the RS256 JWT against the module-level public key
    - Returns {"valid": True, "payload": ...} or {"valid": False, "reason": ...}
- TRUST_DOMAIN reads from env var TRUST_DOMAIN, defaults to "experiment.local"


agents/researcher_agent.py

Keep this as a STUB. Do not add any LLM or tool logic yet.
It should only:
- Call bootstrap("researcher-agent") to get identity
- Print the identity
- Return a hardcoded result string and the identity object

This will be replaced with a real AI agent later.
The identity layer must work independently of agent logic.


verifier/verify.py

A standalone verifier that:
- Accepts a token string
- Calls verify_token() from sdk/bootstrap.py
- Prints whether the identity is VERIFIED or REJECTED
- If verified, prints: SPIFFE ID, agent name, instance ID


main.py

Runs the full experiment end to end:
1. Calls researcher_agent.run("Latest AI agent frameworks")
2. Prints the result
3. Passes the identity token to the verifier
4. Prints verification outcome


requirements.txt

pyjwt
cryptography
python-dotenv


IMPORTANT CONSTRAINTS:

- sdk/ is the shared layer - no agent-specific logic goes in here
- researcher_agent.py only imports from sdk/bootstrap.py
- main.py only imports from agents/ and verifier/
- No circular imports
- No external API calls - this must run fully offline
- Python 3.11+



Phase 2:
Refactor sdk/bootstrap.py into two separate files:

sdk/
|- spire_server.py     ← acts as the SPIRE Server (trust anchor, signing)
|- spire_agent.py      ← acts as the SPIRE Agent (workload API, bootstrap)


sdk/spire_server.py

This simulates the SPIRE Server. Responsibilities:
- Owns the signing key (RSA 2048) - this never leaves this file
- Has a sign_svid(spiffe_id, agent_name, instance_id, trust_domain, ttl_seconds)
  function that mints and returns a signed RS256 JWT
- Has a verify_svid(token) function that verifies a token
  and returns {"valid": True, "payload": ...} or {"valid": False, "reason": ...}
- Has a get_trust_bundle() function that returns the public key
  (equivalent to SPIRE Server's bundle endpoint)
- TRUST_DOMAIN reads from env var TRUST_DOMAIN, defaults to "experiment.local"
- Add a comment on every function explaining which SPIRE Server
  concept it maps to


sdk/spire_agent.py

This simulates the SPIRE Agent (the sidecar equivalent).
Responsibilities:
- Has a bootstrap(agent_name, ttl_seconds=3600) function that:
    - Generates an instance_id (uuid4)
    - Builds the SPIFFE ID: spiffe://<TRUST_DOMAIN>/agent/<agent_name>
    - Calls spire_server.sign_svid() to get a signed token
    - Returns an AgentIdentity object
- Has a verify_token(token) function that:
    - Delegates to spire_server.verify_svid()
- Does NOT own any keys - it only talks to spire_server.py
- Add a comment on every function explaining which SPIRE Agent
  concept it maps to


IMPORTANT CONSTRAINTS:

- spire_server.py never imports from spire_agent.py
- spire_agent.py imports from spire_server.py only
- All other files (researcher_agent.py, verifier/verify.py, main.py)
  update their import from sdk.bootstrap to sdk.spire_agent - 
  the function signatures stay identical so no logic changes
- Delete sdk/bootstrap.py after refactoring
- sdk/identity.py is not touched
- No logic changes anywhere outside sdk/

Phase 3:
Refactor the project structure to support multiple environments.
Move existing local simulation code into a "local" folder and 
add Azure Managed Identity as the production implementation.


NEW PROJECT STRUCTURE
 

agent-identity-experiment/
|- sdk/
│   |- __init__.py
│   |- identity.py                 ← unchanged
│   |- local/
│   │   |- __init__.py
│   │   |- spire_server.py         ← moved from sdk/spire_server.py
│   │   |- spire_agent.py          ← moved from sdk/spire_agent.py
│   |- azure/
│   │   |- __init__.py
│   │   |- spire_server.py         ← new: Azure Managed Identity as trust anchor
│   │   |- spire_agent.py          ← new: Azure equivalent of workload API
│   |- bootstrap.py                ← new: environment router, this is the
│                                      only file agents import from
|- agents/
│   |- researcher_agent.py         ← unchanged, still imports sdk.bootstrap
|- verifier/
│   |- verify.py                   ← unchanged, still imports sdk.bootstrap
|- main.py                         ← unchanged
|- requirements.txt                ← add azure-identity


sdk/bootstrap.py  (environment router)

This is the ONLY file any agent or verifier imports from.
It reads the ENVIRONMENT env var:
  - "local"  → delegates to sdk.local.spire_agent
  - "azure"  → delegates to sdk.azure.spire_agent
  - missing  → defaults to "local", prints a warning

Expose two functions at this level:
  - bootstrap(agent_name, ttl_seconds=3600)
  - verify_token(token)

Both simply delegate to the correct environment implementation.
Add a comment explaining this is the equivalent of the
SPIFFE Workload API endpoint - the single interface all
workloads call regardless of environment.


sdk/local/spire_server.py

Move existing sdk/spire_server.py here. No logic changes.
Add a module-level comment:
  " LOCAL ONLY - simulates SPIRE Server for dev/experiment
   In production this role is played by Azure Managed Identity
   Never use this in production"


sdk/local/spire_agent.py

Move existing sdk/spire_agent.py here. No logic changes.
Add a module-level comment:
   LOCAL ONLY - simulates SPIRE Agent sidecar for dev/experiment
   In production this role is played by sdk/azure/spire_agent.py


sdk/azure/spire_server.py

This replaces the RSA key pair with Azure Managed Identity
as the trust anchor. Responsibilities:

- get_managed_identity_token(resource) function:
    - Uses azure.identity.ManagedIdentityCredential
    - Calls credential.get_token(resource)
    - resource defaults to env var AZURE_RESOURCE,
      fallback "https://management.azure.com/.default"
    - Returns the raw token string
    - Add comment: equivalent to SPIRE Server issuing a JWT-SVID

- verify_svid(token) function:
    - Uses azure.identity.ManagedIdentityCredential to
      get a token for Microsoft Graph
    - Decodes the JWT (no signature check - Azure already
      guarantees it) to extract claims
    - Returns {"valid": True, "payload": ...} or
      {"valid": False, "reason": ...}
    - Add comment: equivalent to SPIRE Server bundle endpoint

- get_trust_bundle() function:
    - Returns the Azure AD JWKS endpoint URL for the tenant
    - Read AZURE_TENANT_ID from env var
    - URL format:
      https://login.microsoftonline.com/<tenant_id>/discovery/keys
    - Add comment: equivalent to SPIRE Server trust bundle endpoint

Add a module-level comment:
   AZURE PRODUCTION - Azure Managed Identity is the trust anchor
   Equivalent role to SPIRE Server in container workloads
   Requires: Managed Identity enabled on the Azure Function
   Requires env vars: AZURE_TENANT_ID, AZURE_RESOURCE (optional)


sdk/azure/spire_agent.py

This is the Azure equivalent of the SPIRE Agent sidecar.
Responsibilities:

- bootstrap(agent_name, ttl_seconds=3600) function:
    - Calls spire_server.get_managed_identity_token()
    - Decodes the token to extract claims (sub, exp, iat)
    - Builds SPIFFE-style ID:
      spiffe://<AZURE_TENANT_ID>/agent/<agent_name>
    - Wraps everything into an AgentIdentity object
    - instance_id comes from the function invocation:
      read WEBSITE_INSTANCE_ID env var (Azure sets this),
      fallback to uuid4
    - Add comment: equivalent to SPIRE Agent workload attestation

- verify_token(token) function:
    - Delegates to spire_server.verify_svid(token)
    - Add comment: equivalent to SPIRE Agent bundle verification

Add a module-level comment:
   AZURE PRODUCTION - equivalent to SPIRE Agent sidecar
   In containers: SPIRE Agent runs as a sidecar
   In Azure Functions: this SDK layer replaces the sidecar


requirements.txt

Add:
  azure-identity
Keep existing:
  pyjwt
  cryptography
  python-dotenv


IMPORTANT CONSTRAINTS

- agents/researcher_agent.py is NOT touched
- verifier/verify.py is NOT touched
- main.py is NOT touched
- sdk/identity.py is NOT touched
- The only import change is inside sdk/bootstrap.py (the router)
- All agents always import from sdk.bootstrap only -
  they never know which environment they are in
- sdk/local/ files must not import from sdk/azure/
- sdk/azure/ files must not import from sdk/local/
- Add a .env.example file showing required env vars:

  ENVIRONMENT=local
  TRUST_DOMAIN=experiment.local
  AZURE_TENANT_ID=your-tenant-id-here
  AZURE_RESOURCE=https://management.azure.com/.default

  Phase 4:

  Add an Azure Functions app to the existing project.
Do not touch any existing files outside the functionapp/ folder.


NEW PROJECT STRUCTURE


agent-identity-experiment/
|- sdk/                          ← unchanged
|- agents/                       ← unchanged
|- verifier/                     ← unchanged
|- main.py                       ← unchanged
|- functionapp/
│   |- host.json
│   |- local.settings.json
│   |- requirements.txt
│   |- AgentTrigger/
│       |- __init__.py
│       |- function.json


functionapp/host.json

Standard Azure Functions v4 host.json.
Set logging level to Information.


functionapp/local.settings.json

Values needed to run locally:
  FUNCTIONS_WORKER_RUNTIME: python
  AzureWebJobsStorage: ""
  ENVIRONMENT: local
  TRUST_DOMAIN: experiment.local
  AZURE_TENANT_ID: your-tenant-id-here
  AZURE_RESOURCE: https://management.azure.com/.default

Add a comment at the top:
   local.settings.json is never deployed to Azure
  In Azure these values are set via app settings
   Switch ENVIRONMENT to "azure" when deploying


functionapp/requirements.txt

azure-functions
azure-identity
pyjwt
cryptography
python-dotenv


functionapp/AgentTrigger/function.json

HTTP trigger that accepts GET and POST.
Route: /api/AgentTrigger
Auth level: anonymous (for local experiment)


functionapp/AgentTrigger/__init__.py

This is the Azure Function entry point.
It wires the existing agent and identity layer
into an HTTP trigger. Responsibilities:

- main(req: func.HttpRequest) -> func.HttpResponse

- Read "task" from query params or request body JSON
  Fallback: "default research task"

- Call agents.researcher_agent.run(task)
  This is the existing stub agent - do not change it

- Call verifier.verify.verify_token(identity.token)
  to verify the identity inside the function itself

- Return a JSON response with:
  {
    "task": <task>,
    "answer": <result answer>,
    "identity": {
      "spiffe_id": <spiffe_id>,
      "agent_name": <agent_name>,
      "instance_id": <instance_id>,
      "expires_at": <expires_at as ISO string>,
      "status": "VALID" or "EXPIRED"
    },
    "verification": {
      "valid": true/false,
      "reason": <reason if invalid>
    },
    "environment": <value of ENVIRONMENT env var>
  }

- If any exception occurs return HTTP 500 with error message

PATH RESOLUTION

The function needs to import from sdk/ and agents/
which live one level above functionapp/.
Add this at the top of __init__.py before any imports:

  import sys
  import os
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

This makes sdk/ agents/ and verifier/ importable
from inside the functionapp/ folder.


IMPORTANT CONSTRAINTS

- Do not modify any file outside functionapp/
- Do not duplicate sdk/ agents/ or verifier/ code
- Do not change researcher_agent.py
- All identity logic stays in sdk/ - none of it
  moves into the function
- The function is just a trigger wrapper -
  it should contain no business logic of its own
- local.settings.json must never be committed -
  add it to .gitignore if one exists
