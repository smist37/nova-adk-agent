#!/usr/bin/env bash
# smoketest.sh — verify the repo passes a clone-and-run test.
#
# Creates a fresh venv in /tmp, installs requirements from scratch, imports
# every public module, and runs the wire-up tests. Intentionally does NOT
# hit the LLM — that's what the eval harness is for.
#
# Exit 0 on success, non-zero on any failure.
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
WORKDIR=$(mktemp -d -t nova-adk-smoketest-XXXXXX)
trap 'rm -rf "$WORKDIR"' EXIT

echo "[smoketest] repo:    $REPO_ROOT"
echo "[smoketest] workdir: $WORKDIR"

# 1. Copy the repo (simulates a fresh clone; real CI would `git clone`).
rsync -a \
    --exclude '.venv' --exclude '__pycache__' \
    --exclude 'eval/results' --exclude 'user_profile.json' \
    --exclude '.env' \
    "$REPO_ROOT"/ "$WORKDIR"/repo/

cd "$WORKDIR/repo"

# 2. Fresh venv.
echo "[smoketest] creating venv..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Install.
echo "[smoketest] pip install -r requirements.txt..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 4. Imports — the public entry points must all load.
echo "[smoketest] importing public modules..."
python - <<'PY'
import nova_adk_agent.hello
import nova_adk_agent.summarize
import nova_adk_agent.summarize_text
import nova_adk_agent.agents
import nova_adk_agent.deploy.vertex
import nova_adk_agent.a2a.server_agent
import nova_adk_agent.a2a.client_agent
print("all modules imported OK")
PY

# 5. Wire-up tests.
echo "[smoketest] running wire-up tests..."
python -m pytest tests/ -v

# 6. Eval harness dry-run (no LLM cost).
echo "[smoketest] eval harness dry-run..."
python -m eval.run --dry-run --quick

echo "[smoketest] PASSED"
