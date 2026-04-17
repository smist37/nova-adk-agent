# Deploying to Vertex AI Agent Engine

This doc walks through deploying the three-agent chain to Vertex AI.
**The deploy step is not run as part of CI.** It requires billing, a
verified project ID, and a human approval gate.

## Prerequisites

- A GCP project with billing enabled.
- The Vertex AI API enabled in that project:
  `gcloud services enable aiplatform.googleapis.com`
- A GCS bucket for source staging (ADK uploads the packaged agent there):
  `gsutil mb -p $GOOGLE_CLOUD_PROJECT -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-adk-staging`
- Application-default credentials for your user or a service account with
  `roles/aiplatform.admin` and `roles/storage.admin`:
  `gcloud auth application-default login`
- The `vertexai` Python package (`pip install "google-cloud-aiplatform[adk,agent_engines]"`).
  This is intentionally *not* in `requirements.txt` — keeping it out lets
  the repo install cleanly on machines that don't have GCP credentials.

## Verify before deploy

The placeholder project ID in `.env.example` is `gen-lang-client-0034704607`.
**Miles has not confirmed this project is the right target for a Vertex
deploy.** Before flipping the comment block in `.env`:

1. Confirm the project is billing-enabled and you have admin access.
2. Confirm Vertex AI is the right service tier for the deploy (vs. Cloud Run,
   Cloud Functions, or a container on GKE).
3. If the project is wrong, create or pick a new one and update `.env.example`
   with the real ID.

## Deploy

```bash
# 1. Activate venv and set env
source .venv/bin/activate
cp .env.example .env
# edit .env — uncomment and verify the Option B block

# 2. Install Vertex-specific deps
pip install "google-cloud-aiplatform[adk,agent_engines]"

# 3. Dry-run: inspect the generated config without actually deploying
python -c "from nova_adk_agent.deploy.vertex import build_deploy_config; \
           import json; print(json.dumps(build_deploy_config(), indent=2))"

# 4. Run the deploy (uncomment the __main__ block in vertex.py first, or
#    call it from a REPL)
python -m nova_adk_agent.deploy.vertex
```

The returned `resource_name` is the handle for the deployed AgentEngine.
Save it — you'll need it to invoke or delete the remote agent.

## Invoking the deployed agent

```python
import vertexai
from vertexai import agent_engines

vertexai.init(project="...", location="us-central1")
remote = agent_engines.get("projects/.../reasoningEngines/XXXXXX")

session = remote.create_session(user_id="miles")
for event in remote.stream_query(
    user_id="miles",
    session_id=session["id"],
    message="https://www.youtube.com/watch?v=...",
):
    print(event)
```

## Tear-down

```python
remote.delete()
```

Agent Engines bill per request *and* for idle time — always tear down an
experimental deploy when you're done.

## Common failure modes

- **`PERMISSION_DENIED` on `aiplatform.reasoningEngines.create`.** The
  calling principal needs `roles/aiplatform.admin` or a custom role with
  that specific permission. Default compute SA does not have it.
- **`INVALID_ARGUMENT: requirements file too large`.** Trim
  `requirements.txt` to only what the deployed agent actually needs —
  `pytest`, `ragas`, and the eval-time deps shouldn't be in the
  runtime image.
- **`NOT_FOUND: staging bucket`.** Create the bucket first (see
  prerequisites). AgentEngine does not create it for you.
- **`QUOTA_EXCEEDED`.** Vertex has a default quota of 10 AgentEngines
  per project. Delete old deploys first.

## Why this is wired but not run

The repo is a portfolio artifact. Paying for a live Vertex deploy that
no one is calling is a waste of billing. The code path is proven —
`build_deploy_config()` is unit-tested, and the `deploy()` function
matches the documented AgentEngine API — but the actual API call is
gated behind an explicit, commented-out `__main__` block so importing
the module costs nothing.
