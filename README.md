# Serverless Agent Identity

Proof of concept: give a serverless AI agent a cryptographic identity — the same idea as SPIRE/SPIFFE for containers, but without a sidecar.

Every agent that bootstraps gets a signed JWT (a JWT-SVID) with a SPIFFE-style ID:
```
spiffe://<trust_domain>/agent/<agent_name>
```

In local mode an in-process RSA key pair acts as the trust anchor. In Azure, that role is played by Managed Identity — the platform issues the token, no keys to manage.

---

## How it works

```
sdk/bootstrap.py          ← single entry point, reads ENVIRONMENT env var
  ├── sdk/local/          ← RSA key pair, self-signed JWT  (dev/experiment)
  └── sdk/azure/          ← Azure Managed Identity         (production)
```

Agents always import from `sdk.bootstrap` only. They never know which environment they're in.

---

## Run locally

**Prerequisites:** Python 3.11+, packages installed

```bash
pip install -r requirements.txt
```

Run the end-to-end experiment:
```bash
python main.py
```

You should see the agent bootstrap with a SPIFFE ID and the verifier confirm it as `VERIFIED`.

To test it as an HTTP function, install [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) then:

```bash
pip install -r functionapp/requirements.txt --target functionapp/.python_packages/lib/site-packages

cd functionapp
func start
```

In another terminal:
```bash
curl "http://localhost:7071/api/AgentTrigger?task=AI+agent+frameworks"
```

---

## Deploy to Azure

**1. Create resources**
```bash
az group create --name rg-agent-identity --location eastus

az storage account create --name sagentidentity \
  --resource-group rg-agent-identity --sku Standard_LRS

az functionapp create \
  --name agent-identity-func \
  --resource-group rg-agent-identity \
  --storage-account sagentidentity \
  --consumption-plan-location eastus \
  --runtime python --runtime-version 3.11 --os-type linux
```

**2. Enable Managed Identity**
```bash
az functionapp identity assign \
  --name agent-identity-func \
  --resource-group rg-agent-identity
```

**3. Copy shared packages into the function folder and publish**
```bash
cp -r sdk agents verifier functionapp/

cd functionapp
func azure functionapp publish agent-identity-func --python
```

**4. Set app settings**
```bash
az functionapp config appsettings set \
  --name agent-identity-func \
  --resource-group rg-agent-identity \
  --settings \
    ENVIRONMENT=azure \
    AZURE_TENANT_ID=$(az account show --query tenantId -o tsv)
```

**5. Test it**
```bash
curl "https://agent-identity-func.azurewebsites.net/api/AgentTrigger?task=AI+agent+frameworks"
```

The response will include the agent's identity, the SPIFFE ID, and whether it verified — now backed by Azure Managed Identity instead of a local key pair.

---

## Project structure

```
sdk/
  identity.py          AgentIdentity dataclass
  bootstrap.py         environment router (the only file agents import from)
  local/               local trust anchor — RSA key pair, RS256 JWT signing
  azure/               Azure trust anchor — Managed Identity token

agents/
  researcher_agent.py  stub agent (replace with real LLM agent later)

verifier/
  verify.py            standalone token verifier

functionapp/
  AgentTrigger/        HTTP-triggered Azure Function

main.py                local end-to-end runner
```

---

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | `local` or `azure` | `local` (with warning) |
| `TRUST_DOMAIN` | Trust domain for local mode | `experiment.local` |
| `AZURE_TENANT_ID` | Azure AD tenant ID (azure mode) | — |
| `AZURE_RESOURCE` | Resource scope for MI token | `https://management.azure.com/.default` |

Copy `.env.example` to `.env` to set these for local runs.
