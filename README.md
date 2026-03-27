---
title: OpenEnv Email Triage
sdk: docker
app_port: 7860
tags:
  - openenv
  - email-triage
  - reinforcement-learning
---

# OpenEnv Email Triage

A complete, real-world OpenEnv environment where an AI agent learns to triage operational inboxes.

This environment simulates work that human support and operations teams perform every day:

- detect spam and phishing
- route legal/security issues to the right teams
- prioritize urgent incidents
- draft useful customer replies

It implements standard `step()` / `reset()` / `state()` APIs with typed Pydantic models, deterministic task graders, shaped rewards, baseline inference, and containerized deployment for Hugging Face Spaces.

## Why This Environment

Email triage is a practical autonomy benchmark: agents must classify intent, make safe routing decisions, and communicate clearly under step budgets. The task naturally supports partial credit and policy penalties.

## OpenEnv API

Core environment class: `EmailTriageEnv` in `src/openenv_email_triage/environment.py`.

- `reset(task_id: Optional[str]) -> Observation`
- `step(action: Action) -> tuple[Observation, Reward, bool, dict]`
- `state() -> EnvState`

Typed models are defined in `src/openenv_email_triage/models.py`:

- `Observation`
- `Action`
- `Reward`
- `EnvState`

Metadata is in `openenv.yaml`.

## Action Space

`Action` supports:

- `classify` (`email_id`, `label`)
- `set_priority` (`email_id`, `priority`)
- `draft_reply` (`email_id`, `message`)
- `archive` (`email_id`)
- `escalate` (`email_id`, `team`)
- `noop` (`reason` optional)

Labels: `billing`, `technical`, `sales`, `hr`, `spam`, `other`.

Priority values: `low`, `medium`, `high`.

## Observation Space

`Observation` contains:

- current task id and instruction
- step count and max steps
- inbox snapshot (email objects with mutable fields)
- recent action history

## Tasks and Graders

All tasks are deterministic and scored from `0.0` to `1.0` by programmatic graders in `src/openenv_email_triage/graders.py`.

1. `easy_invoice_spam` (easy)
- classify/clear obvious spam
- correctly triage and respond to invoice issue

2. `medium_ops_queue` (medium)
- route outage to engineering
- prioritize incident correctly
- respond to sales lead and classify HR query

3. `hard_risk_and_vip` (hard)
- identify phishing and escalate to security
- route legal risk properly with timeline response
- handle VIP P1 issue with escalation and ETA communication

## Reward Function

Reward is shaped across the whole trajectory:

- primary signal: grader progress delta at each step
- completion bonus when objective reaches full score
- penalties for invalid actions, missing email ids, unnecessary archive behavior (hard task), and `noop` loops

This provides dense partial credit while discouraging destructive or unproductive behavior.

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
set PYTHONPATH=src
# macOS/Linux: export PYTHONPATH=src
```

## Local Usage

Run API server:

```bash
uvicorn openenv_email_triage.app:app --host 0.0.0.0 --port 7860
```

Run tests:

```bash
pytest -q
```

Validate metadata (if OpenEnv CLI installed):

```bash
openenv validate
```

## Baseline Inference Script

Baseline runner (`scripts/run_baseline.py`) uses the OpenAI API client and reads credentials from `OPENAI_API_KEY`.

```bash
set OPENAI_API_KEY=your_key_here
python scripts/run_baseline.py --model gpt-4.1-mini
```

The script runs all 3 tasks with deterministic prompting (`temperature=0`, fixed seed) and prints per-task + average scores.

### Reproducible Baseline Scores

Expected baseline range with `gpt-4.1-mini` and default prompts:

- `easy_invoice_spam`: `0.8 - 1.0`
- `medium_ops_queue`: `0.6 - 0.85`
- `hard_risk_and_vip`: `0.45 - 0.75`
- average: `~0.62 - 0.87`

Exact score can vary slightly across model snapshots, but setup and task data are deterministic.

## Docker

Build and run:

```bash
docker build -t openenv-email-triage .
docker run --rm -p 7860:7860 openenv-email-triage
```

The container starts a FastAPI app on port `7860`.

## Hugging Face Spaces Deployment (Docker)

1. Create a new Space with **SDK = Docker**.
2. Push this repository to the Space.
3. In Space settings, add tag `openenv`.
4. Optionally add secret `OPENAI_API_KEY` for running baseline scripts in the Space.
5. Space builds from the included `Dockerfile` and serves the API.

## Project Structure

```text
src/openenv_email_triage/
  app.py
  baseline.py
  environment.py
  graders.py
  models.py
  tasks.py
scripts/run_baseline.py
openenv.yaml
Dockerfile
README.md
tests/test_env.py
```
