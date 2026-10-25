# Sonora · Django AI Music Studio

A local music studio using the real ACE-Step 1.5 asynchronous REST API. Django serves a responsive composer, SQLite track history, generation status, and locally saved audio with playback and downloads. Supports prompts, lyrics, instrumental tracks, tempo, duration, and reproducible seeds. No synthetic demo audio is presented as AI output.

## Run Django

Requires Python 3.12+ (tested here on Python 3.14).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Open http://127.0.0.1:8000. The studio works without an engine, but generation requires ACE-Step. Offline requests show a clear error and retain the failed attempt in your library.

## Install and run ACE-Step 1.5

Official engine: https://github.com/ace-step/ACE-Step-1.5
Official API: https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md

The engine has its own Python 3.11/3.12 environment; keep it separate from Django. Core model weights need approximately 10 GB, plus dependencies and audio storage. Reserve at least 15 GB free. Models download at first launch. CUDA is recommended; macOS MPS and CPU are supported upstream, with hardware-dependent performance.

Install uv using https://docs.astral.sh/uv/getting-started/installation/ then:

```bash
./scripts/setup-engine.sh
./scripts/start-engine.sh
```

The API should listen on http://127.0.0.1:8001. DiT-only mode disables the optional language model to reduce resource requirements. The studio uses eight turbo inference steps and a single MP3 output. For a different engine address or protected engine, export `ACESTEP_URL` and `ACESTEP_API_KEY` before starting Django. `.env.example` documents variables; `.env` files are not loaded automatically.

Workflow: `POST /release_task` → `POST /query_result` → authenticated `/v1/audio` download → local media file. Refreshing the studio resumes polling saved running tasks. Keep a browser tab open while generating; a separate background job queue is not included. Delete removes the local track and its file, not any still-running engine task. Intended for a single trusted local user; no account isolation or production job workers are included.

## Verification

```bash
.venv/bin/python manage.py test
.venv/bin/python manage.py check
```

Eight tests cover rendering, validation, CSRF, official API submission, offline failures, mocked job completion/audio persistence/playback/download/deletion, foreign audio URL rejection, and engine status handling. These are contract tests with mocked model responses, not inference quality tests.

On the development machine, real inference could not be tested: only 4.4 GB disk space was available, less than the documented core model storage requirement. The engine/model weights have not been installed. Django runs independently and the real offline path is verified.

The development server binds only to loopback. Before network deployment add authentication, a durable worker queue, deployment settings, HTTPS, and storage quotas. Optional Django admin: `.venv/bin/python manage.py createsuperuser`.

## Vercel

Import this repository with the Django framework preset. Vercel serves static files automatically. Pushes to main deploy production. Set DJANGO_SECRET_KEY privately, DATABASE_URL to PostgreSQL, and ACESTEP_URL to your reachable inference API (plus ACESTEP_API_KEY when required). Run migrations against that database before enabling generation. Without DATABASE_URL, the studio renders but explicitly disables generation and explains the missing setup. Vercel cannot reach your computer's localhost engine. Audio in /tmp is temporary; durable cloud audio storage is still required before relying on saved audio across instances or deployments.
