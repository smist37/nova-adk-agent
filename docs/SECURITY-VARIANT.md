# Security-focused variant — air-gapped deployment

**Status:** design + Dockerfile (`Dockerfile.airgap`). The image
builds and runs cleanly. What's *not* done: the actual swap of
Gemini for a local inference endpoint inside the agent code. The
routing stub (`nova_adk_agent/routing/router.py`) has the
classification-aware gate to keep sensitive traffic local, but the
code paths that currently call `gemini-2.5-flash` directly have not
been rewritten to honor the router.

This is the cleared-AI-engineer moat: a version of the agent that
runs inside an air-gapped, IL-5/6 or comparable restricted
environment where:

- The container has no outbound internet.
- Commercial LLM APIs (Gemini, OpenAI, Anthropic) are unreachable by
  policy, not just by config.
- Model weights run locally — typically vLLM or TGI serving Llama /
  Nous Hermes / Mistral.
- User data (profiles, transcripts) stays inside the enclave.

## Threat model

- **Exfil risk.** Any egress network call is a potential data leak.
  The container must not reach the public internet — including for
  dependency resolution, model calls, telemetry, or crash reporting.
- **Dependency supply chain.** Wheels must be pre-vetted before they
  enter the enclave. `pip install` at runtime is forbidden; every
  wheel must be pulled in a reviewable build step.
- **Credential sprawl.** No API keys in the container. No
  `GOOGLE_API_KEY`. If one leaks into the image, the whole thing
  fails a security review.
- **Runtime container posture.** Runs as a non-root user, no shell
  login, minimal filesystem footprint, explicit volume for user
  data.

The Dockerfile addresses all of these. What it *doesn't* address is
the agent code assuming a live Gemini API — that's the work still
to do (see "Not done" below).

## How the Dockerfile works

Two stages:

1. **`wheel-builder`** (has internet). Downloads every wheel the
   agent needs into `/wheels`. Runs only on a network-connected
   build host.
2. **Runtime image** (no internet expected). Installs wheels offline
   via `pip install --no-index --find-links /wheels`. Drops wheels
   after install to keep the image small.

Build → save → ship → load → run.

Runtime defaults are paranoid: `GOOGLE_API_KEY=""` is set explicitly
to blank. `GOOGLE_GENAI_USE_VERTEXAI=FALSE`. The agent runs as
non-root. The only network endpoint the agent expects is
`LOCAL_LLM_URL`, which points at a vLLM server on the host network.

## What's not done

The actual swap. The agent code currently hard-codes
`gemini-2.5-flash`. For a real air-gapped deploy the work is:

1. Replace each `Agent(model="gemini-2.5-flash", ...)` with a call
   to the router, which returns an open-weight model for the
   sensitive / classified privacy class.
2. Wire ADK's LLM abstraction to a vLLM-backed client. ADK
   supports OpenAI-compatible endpoints — vLLM speaks that — so
   this is mostly config.
3. Expose a privacy-class signal from the caller. Today there's no
   way for a user to say "this transcript is classified" — the
   router can't make the right decision without the signal.
4. Add a preflight check that fails loudly if any `Agent()` in the
   loaded chain has a `model=` pointing at a commercial endpoint
   when the runtime is tagged air-gapped.

Each of these is tractable — the shape is already here — but none
of them are wired into `main`. This is a portfolio artifact, not a
live air-gapped deploy.

## Why this is documented even though it's not fully built

Cleared-AI work is *the* career lane this repo targets. Reviewers in
that lane want to see that the developer understands the constraints
(no egress, no commercial API keys, wheel provenance, non-root
runtime) even if the specific project hasn't been stamped for
production. The Dockerfile + this doc together demonstrate the
understanding.

A real air-gapped build is a 2-4 week project on top of this one:
- vLLM serving Llama-3 or Nous Hermes, sized for available hardware.
- Model weights staged through the same review process as the wheels.
- Logging / observability that doesn't phone home (Prometheus local,
  no SaaS sinks).
- Hardened base image, not `python:3.11-slim` — something Chainguard
  or Wolfi-distroless.
- Accreditation paperwork, which is half the job.

## Reviewer checklist (for when this does get built)

- [ ] No `GOOGLE_*` env vars present at runtime beyond
      `GOOGLE_GENAI_USE_VERTEXAI=FALSE`.
- [ ] `curl https://generativelanguage.googleapis.com` fails inside
      the container.
- [ ] All wheels in the image are pre-vetted (hash-pinned, SBOM
      generated, known-CVE-clean).
- [ ] Agent process runs as non-root.
- [ ] No writable filesystem locations except the mounted
      `USER_PROFILE_DIR`.
- [ ] Healthcheck does not call any LLM.
- [ ] Agent declines gracefully if `LOCAL_LLM_URL` is unreachable —
      no silent fallback to any other endpoint.
