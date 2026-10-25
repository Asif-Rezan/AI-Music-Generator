#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v uv >/dev/null; then
  echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/'
  exit 1
fi
available=$(df -Pk . | awk 'NR==2 {print $4}')
if [ "$available" -lt 15728640 ]; then
  echo 'ACE-Step needs space for models and dependencies. Free at least 15 GB before setup.'
  exit 1
fi
if [ ! -d .acestep ]; then
  git clone https://github.com/ace-step/ACE-Step-1.5.git .acestep
fi
cd .acestep
uv sync --python 3.12
printf '\nReady. Start with: ./scripts/start-engine.sh\n'
