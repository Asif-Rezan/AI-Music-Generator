#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.acestep"
export ACESTEP_INIT_LLM=false
export ACESTEP_LM_BACKEND=pt
exec uv run acestep-api
