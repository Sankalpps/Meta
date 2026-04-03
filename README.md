<<<<<<< HEAD
---
title: OpenEnv Multi-Agent Intersection Control
sdk: docker
app_port: 7860
tags:
  - openenv
  - traffic-control
  - multi-agent
  - emergency-priority
---

# OpenEnv Multi-Agent Intersection Control

A complete real-world OpenEnv environment where an AI system manages a four-way urban intersection and prioritizes emergency vehicles.

## Real-World Task Simulation

This environment models a real operational task performed by traffic control centers:

- optimize vehicle throughput at a 4-way intersection
- prevent unsafe conflicting green phases
- prioritize emergency vehicles (ambulance/fire/police) with minimal delay
- maintain fairness under congestion waves

This is not a toy game; it simulates a practical safety-critical control problem.

## OpenEnv Spec Compliance

Core environment class: `IntersectionEnv` in `src/openenv_intersection/environment.py`.

Implemented API:

- `reset(task_id: Optional[str]) -> Observation`
- `step(action: Action) -> tuple[Observation, Reward, bool, dict]`
- `state() -> EnvState`

Typed Pydantic models in `src/openenv_intersection/models.py`:

- `Observation`
- `Action`
- `Reward`
- `EnvState`

Metadata file for validators: `openenv.yaml`.

## Action and Observation Spaces

Action space:

- `set_phase` with 4 directional light assignments
- `preempt_emergency` for targeted emergency corridor control
- `hold` for keeping current phase briefly

Observation space includes:

- per-direction queue lengths
- per-direction signal state
- active emergency vehicles (`eta_steps`, `waited_steps`, `crossed`)
- throughput and safety violations
- recent events

## Tasks and Agent Graders (Easy -> Hard)

All tasks are deterministic and scored by a programmatic grader (`0.0` to `1.0`) in `src/openenv_intersection/graders.py`.

1. `easy_single_ambulance` (easy)
- moderate traffic with one ambulance event
- objective: clear emergency quickly while keeping steady flow

2. `medium_peak_with_firetruck` (medium)
- peak-hour arrival surges with one firetruck event
- objective: maintain safety and reduce congestion while prioritizing emergency

3. `hard_dual_emergency_wave` (hard)
- sustained congestion plus two conflicting emergency events
- objective: coordinate safe preemption and balanced control under pressure

## Meaningful Reward Function

The reward provides dense trajectory-level signal:

- positive: grader progress delta and vehicles moved
- penalties: conflicting greens, invalid phases, blocked emergency paths
- terminal bonus: objective completion with strong score

This supports incremental learning and discourages undesirable policies.

## Baseline Inference Script

- Script: `scripts/run_intersection_baseline.py`
- Uses OpenAI API when `OPENAI_API_KEY` is available
- Falls back to deterministic heuristic policy when key is missing/invalid
- Outputs reproducible per-task scores and average

Run:

```bash
# Windows PowerShell
$env:OPENAI_API_KEY='your_key_here'
.\.venv\Scripts\python.exe scripts/run_intersection_baseline.py --model gpt-4.1-mini
```

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

Run server:

```bash
python -m uvicorn openenv_intersection.app:app --host 0.0.0.0 --port 7860
```

Test suite:

```bash
pytest -q
```

Optional validator (if official OpenEnv CLI is installed):

```bash
openenv validate
```

## Docker and Hugging Face Spaces

Build and run locally:

```bash
docker build -t openenv-intersection .
docker run --rm -p 7860:7860 openenv-intersection
```

Space URL:

- `https://huggingface.co/spaces/Sankalpps/openenv-email-triage`

The current `Dockerfile` launches `openenv_intersection.app:app`.

## Project Structure

```text
src/openenv_intersection/
  app.py
  baseline.py
  environment.py
  graders.py
  models.py
  tasks.py
scripts/run_intersection_baseline.py
openenv.yaml
Dockerfile
README.md
tests/test_intersection_env.py
```
=======
---
title: OpenEnv Multi-Agent Intersection Control
sdk: docker
app_port: 7860
tags:
  - openenv
  - traffic-control
  - multi-agent
  - emergency-priority
---

# OpenEnv Multi-Agent Intersection Control

A complete real-world OpenEnv environment where an AI system manages a four-way urban intersection and prioritizes emergency vehicles.

## Real-World Task Simulation

This environment models a real operational task performed by traffic control centers:

- optimize vehicle throughput at a 4-way intersection
- prevent unsafe conflicting green phases
- prioritize emergency vehicles (ambulance/fire/police) with minimal delay
- maintain fairness under congestion waves

This is not a toy game; it simulates a practical safety-critical control problem.

## OpenEnv Spec Compliance

Core environment class: `IntersectionEnv` in `src/openenv_intersection/environment.py`.

Implemented API:

- `reset(task_id: Optional[str]) -> Observation`
- `step(action: Action) -> tuple[Observation, Reward, bool, dict]`
- `state() -> EnvState`

Typed Pydantic models in `src/openenv_intersection/models.py`:

- `Observation`
- `Action`
- `Reward`
- `EnvState`

Metadata file for validators: `openenv.yaml`.

## Action and Observation Spaces

Action space:

- `set_phase` with 4 directional light assignments
- `preempt_emergency` for targeted emergency corridor control
- `hold` for keeping current phase briefly

Observation space includes:

- per-direction queue lengths
- per-direction signal state
- active emergency vehicles (`eta_steps`, `waited_steps`, `crossed`)
- throughput and safety violations
- recent events

## Tasks and Agent Graders (Easy -> Hard)

All tasks are deterministic and scored by a programmatic grader (`0.0` to `1.0`) in `src/openenv_intersection/graders.py`.

1. `easy_single_ambulance` (easy)
- moderate traffic with one ambulance event
- objective: clear emergency quickly while keeping steady flow

2. `medium_peak_with_firetruck` (medium)
- peak-hour arrival surges with one firetruck event
- objective: maintain safety and reduce congestion while prioritizing emergency

3. `hard_dual_emergency_wave` (hard)
- sustained congestion plus two conflicting emergency events
- objective: coordinate safe preemption and balanced control under pressure

## Meaningful Reward Function

The reward provides dense trajectory-level signal:

- positive: grader progress delta and vehicles moved
- penalties: conflicting greens, invalid phases, blocked emergency paths
- terminal bonus: objective completion with strong score

This supports incremental learning and discourages undesirable policies.

## Baseline Inference Script

- Script: `scripts/run_intersection_baseline.py`
- Uses OpenAI API when `OPENAI_API_KEY` is available
- Falls back to deterministic heuristic policy when key is missing/invalid
- Outputs reproducible per-task scores and average

Run:

```bash
# Windows PowerShell
$env:OPENAI_API_KEY='your_key_here'
.\.venv\Scripts\python.exe scripts/run_intersection_baseline.py --model gpt-4.1-mini
```

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

Run server:

```bash
python -m uvicorn openenv_intersection.app:app --host 0.0.0.0 --port 7860
```

Test suite:

```bash
pytest -q
```

Optional validator (if official OpenEnv CLI is installed):

```bash
openenv validate
```

## Docker and Hugging Face Spaces

Build and run locally:

```bash
docker build -t openenv-intersection .
docker run --rm -p 7860:7860 openenv-intersection
```

Space URL:

- `https://huggingface.co/spaces/Sankalpps/openenv-email-triage`

The current `Dockerfile` launches `openenv_intersection.app:app`.

## Project Structure

```text
src/openenv_intersection/
  app.py
  baseline.py
  environment.py
  graders.py
  models.py
  tasks.py
scripts/run_intersection_baseline.py
openenv.yaml
Dockerfile
README.md
tests/test_intersection_env.py
```
>>>>>>> 6d513dca441eccedd7df32d75f565ad9c470a888
