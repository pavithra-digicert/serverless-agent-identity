# Serverless Agent Identity

Proof of concept: Give a serverless AI agent a cryptographic identity - the same idea as SPIRE/SPIFFE for containers, but without a sidecar.

Every agent that bootstraps gets a signed JWT (a JWT-SVID) with a SPIFFE-style ID:
```
spiffe://<trust_domain>/agent/<agent_name>
```

In local mode an in-process RSA key pair acts as the trust anchor. In Azure, that role is played by Managed Identity - the platform issues the token, no keys to manage.

The agent code (`agents/`) and the identity SDK (`sdk/`) are completely separate. Agents call one function - `bootstrap()` - and get back a signed identity. 

For this POC, the `sdk/` folder is shared by physically copying it into the deployment package.

- **An installable Python library** - agents just `pip install agent-identity-sdk` and import from it, the same way they'd import any other package.
- **An HTTP service** - agents call a local sidecar or a central identity endpoint to get their token, similar to how SPIRE's Workload API works over a Unix socket. The agent never holds any key material at all.

Next Step: Currently researcher-agent is a stub. Use an agent to convey the concept. 
---


## Environment variables

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | `local` or `azure` | `local` (with warning) |
| `TRUST_DOMAIN` | Trust domain for local mode | `experiment.local` |
| `AZURE_TENANT_ID` | Azure AD tenant ID (azure mode) | - |
| `AZURE_RESOURCE` | Resource scope for MI token | `https://management.azure.com/.default` |

Copy `.env.example` to `.env` to set these for local runs.
