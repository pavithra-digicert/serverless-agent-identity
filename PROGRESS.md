# What we built and where this goes next

## What this proves

This project moves the trust logic into the SDK layer, so every agent gets identity on bootstrap without any infrastructure change.

---

## What was built

**A SPIRE-equivalent identity layer**

The agent code (`agents/`) and the identity SDK (`sdk/`) are completely separate. Agents call one function — `bootstrap()` — and get back a signed identity. They have no idea how it was issued or which environment they're running in. That separation is the point.

For this POC, the `sdk/` folder is shared by physically copying it into the deployment package. That's intentional — it keeps the experiment self-contained and easy to run. In a real setup, `sdk/` would graduate into one of two things:

- **An installable Python library** — agents just `pip install agent-identity-sdk` and import from it, the same way they'd import any other package. No folder copying, no path manipulation.
- **An HTTP service** — agents call a local sidecar or a central identity endpoint to get their token, similar to how SPIRE's Workload API works over a Unix socket. The agent never holds any key material at all.

---

## What this does not do yet

- The researcher agent is a stub. It returns a hardcoded string. No LLM, no tools. It just mimcs a serverless agent that doe snot run forever. 

---
