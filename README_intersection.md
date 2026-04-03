<<<<<<< HEAD
# OpenEnv Multi-Agent Intersection Control

Real-world OpenEnv environment where an AI traffic controller manages a 4-way intersection and prioritizes emergency vehicles.

## Real-World Motivation

Urban traffic control centers must optimize throughput and safety while guaranteeing emergency vehicle right-of-way. This environment models the same operational constraints through deterministic scenarios and measurable outcomes.

## OpenEnv API

Core class: `IntersectionEnv` in `src/openenv_intersection/environment.py`.

- `reset(task_id: Optional[str]) -> Observation`
- `step(action: Action) -> tuple[Observation, Reward, bool, dict]`
- `state() -> EnvState`

Metadata file: `openenv_intersection.yaml`.

## Multi-Agent Framing

The system controls four signal agents (north, south, east, west) under a central policy. Actions can set per-direction lights or trigger emergency preemption by approach.

## Action Space

- `set_phase`: provide four directional light states
- `preempt_emergency`: force green corridor for emergency approach/opposite lane
- `hold`: keep current phase briefly

## Observation Space

- per-direction queue lengths
- current light state per direction
- active emergency vehicles (eta, waited, crossed)
- throughput and safety violations

## Tasks (Easy -> Hard)

1. `easy_single_ambulance`
- Single emergency under moderate flow.

2. `medium_peak_with_firetruck`
- Peak congestion plus one high-priority emergency.

3. `hard_dual_emergency_wave`
- Two conflicting emergency events under sustained congestion.

## Reward Design

Dense shaping encourages incremental progress:

- positive reward for throughput and grader progress delta
- penalties for conflicting greens (safety), invalid phases, and emergency blocking
- terminal bonus for achieving high score after emergency clearance

## Baseline

Runs with OpenAI API client and deterministic settings:

```bash
set OPENAI_API_KEY=your_key
set PYTHONPATH=src
python scripts/run_intersection_baseline.py --model gpt-4.1-mini
```

## Local Run

```bash
set PYTHONPATH=src
python -m uvicorn openenv_intersection.app:app --host 0.0.0.0 --port 7860
```

## Docker

Current `Dockerfile` already launches this intersection app:

```text
uvicorn openenv_intersection.app:app --host 0.0.0.0 --port 7860
```
=======
# OpenEnv Multi-Agent Intersection Control

Real-world OpenEnv environment where an AI traffic controller manages a 4-way intersection and prioritizes emergency vehicles.

## Real-World Motivation

Urban traffic control centers must optimize throughput and safety while guaranteeing emergency vehicle right-of-way. This environment models the same operational constraints through deterministic scenarios and measurable outcomes.

## OpenEnv API

Core class: `IntersectionEnv` in `src/openenv_intersection/environment.py`.

- `reset(task_id: Optional[str]) -> Observation`
- `step(action: Action) -> tuple[Observation, Reward, bool, dict]`
- `state() -> EnvState`

Metadata file: `openenv_intersection.yaml`.

## Multi-Agent Framing

The system controls four signal agents (north, south, east, west) under a central policy. Actions can set per-direction lights or trigger emergency preemption by approach.

## Action Space

- `set_phase`: provide four directional light states
- `preempt_emergency`: force green corridor for emergency approach/opposite lane
- `hold`: keep current phase briefly

## Observation Space

- per-direction queue lengths
- current light state per direction
- active emergency vehicles (eta, waited, crossed)
- throughput and safety violations

## Tasks (Easy -> Hard)

1. `easy_single_ambulance`
- Single emergency under moderate flow.

2. `medium_peak_with_firetruck`
- Peak congestion plus one high-priority emergency.

3. `hard_dual_emergency_wave`
- Two conflicting emergency events under sustained congestion.

## Reward Design

Dense shaping encourages incremental progress:

- positive reward for throughput and grader progress delta
- penalties for conflicting greens (safety), invalid phases, and emergency blocking
- terminal bonus for achieving high score after emergency clearance

## Baseline

Runs with OpenAI API client and deterministic settings:

```bash
set OPENAI_API_KEY=your_key
set PYTHONPATH=src
python scripts/run_intersection_baseline.py --model gpt-4.1-mini
```

## Local Run

```bash
set PYTHONPATH=src
python -m uvicorn openenv_intersection.app:app --host 0.0.0.0 --port 7860
```

## Docker

Current `Dockerfile` already launches this intersection app:

```text
uvicorn openenv_intersection.app:app --host 0.0.0.0 --port 7860
```
>>>>>>> 6d513dca441eccedd7df32d75f565ad9c470a888
