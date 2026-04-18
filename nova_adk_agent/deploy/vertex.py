"""Vertex AI deploy wiring for the three-agent podcast synthesizer.

This module is intentionally *wired but inert*. The ``deploy()`` call is
commented out so importing this module has zero side effects — no GCP calls,
no billing, no surprise. To actually deploy:

1. Verify ``GOOGLE_CLOUD_PROJECT`` in ``.env`` points at a billing-enabled
   project with Vertex AI enabled. Project ID should be verified before
   running — the default in ``.env.example`` is a placeholder.
2. ``gcloud auth application-default login``
3. Uncomment the ``deploy()`` call at the bottom of this module, or import
   and call it from a REPL.

See ``docs/DEPLOY.md`` for the full checklist and common failure modes.
"""
from __future__ import annotations

import os
from pathlib import Path

# Reasonable Vertex defaults — override via env or the config constants below.
DEFAULT_LOCATION = "us-central1"
DEFAULT_STAGING_BUCKET_TEMPLATE = "gs://{project}-adk-staging"
DEFAULT_DISPLAY_NAME = "nova-adk-podcast-synthesizer"
DEFAULT_DESCRIPTION = (
    "Three-agent ADK chain: coordinator -> summarizer -> formatter. "
    "Fetches podcast transcripts and produces personalized syntheses."
)


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing env var {name}. Set it in .env (see .env.example) "
            "or export it before calling deploy()."
        )
    return value


def build_deploy_config() -> dict:
    """Build the Vertex AgentEngine deploy config from env vars.

    Exposed as a pure function so the CI/CD workflow and unit tests can
    inspect the config without triggering a real deploy.
    """
    project = _require_env("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", DEFAULT_LOCATION)
    staging_bucket = os.environ.get(
        "GOOGLE_CLOUD_STAGING_BUCKET",
        DEFAULT_STAGING_BUCKET_TEMPLATE.format(project=project),
    )
    requirements = (
        Path(__file__).resolve().parent / "requirements.txt"
    )
    return {
        "project": project,
        "location": location,
        "staging_bucket": staging_bucket,
        "display_name": DEFAULT_DISPLAY_NAME,
        "description": DEFAULT_DESCRIPTION,
        "requirements_file": str(requirements),
    }


def deploy() -> str:
    """Deploy the root agent to Vertex AI Agent Engine.

    Returns the resource name of the deployed AgentEngine. This function is
    NOT called on import — it's gated behind an explicit call at module
    level (currently commented out) or from a REPL. Never wire this into
    CI without an explicit human approval gate.
    """
    # Imports are inside the function so ``import nova_adk_agent.deploy.vertex``
    # remains safe in environments where ``vertexai`` isn't installed (e.g.,
    # local dev that only uses the Gemini API path).
    import vertexai  # type: ignore
    from vertexai import agent_engines  # type: ignore

    from nova_adk_agent.agents import root_agent

    cfg = build_deploy_config()
    vertexai.init(
        project=cfg["project"],
        location=cfg["location"],
        staging_bucket=cfg["staging_bucket"],
    )
    import subprocess, os
    # Build a wheel into the repo root so the relative path passed to
    # extra_packages results in a flat entry in dependencies.tar.gz.
    # The container startup script runs `pip install *.whl` at tar root level,
    # so absolute paths (which get stored with full dir structure) are never found.
    repo_root = Path(__file__).resolve().parent.parent.parent
    subprocess.run(
        ["python", "-m", "build", "--wheel", "--outdir", str(repo_root), str(repo_root)],
        check=True, capture_output=True,
    )
    wheels = list(repo_root.glob("nova_adk_agent-*.whl"))
    # Change to repo root so tarfile.add() stores just the filename (flat).
    orig_dir = os.getcwd()
    os.chdir(repo_root)
    try:
        remote_agent = agent_engines.create(
            agent_engine=root_agent,
            display_name=cfg["display_name"],
            description=cfg["description"],
            requirements=cfg["requirements_file"],
            extra_packages=[w.name for w in wheels],
        )
    finally:
        os.chdir(orig_dir)
        for w in wheels:
            w.unlink(missing_ok=True)
    return remote_agent.resource_name


# -----------------------------------------------------------------------------
# Deliberately commented out. Uncomment only after reading docs/DEPLOY.md.
# -----------------------------------------------------------------------------
# if __name__ == "__main__":
#     resource_name = deploy()
#     print(f"Deployed: {resource_name}")
