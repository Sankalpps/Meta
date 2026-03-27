from __future__ import annotations

import json
import os

from openai import OpenAI

from .environment import IntersectionEnv
from .graders import grade_task
from .models import Action, Direction, LightState, SignalAction


SYSTEM_PROMPT = (
    "You control a four-way traffic intersection with emergency-vehicle preemption. "
    "Return exactly one JSON action per turn. Keep signals safe and prioritize emergencies."
)

_OPPOSITE = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
}


def _heuristic_action(observation: dict) -> Action:
    emergency = observation.get("emergency_vehicles", [])
    ready = [
        ev
        for ev in emergency
        if not ev.get("crossed", False) and int(ev.get("eta_steps", 99)) <= 1
    ]

    if ready:
        return Action(
            action_type="preempt_emergency",
            target_direction=ready[0]["approach"],
            reason="heuristic_emergency_priority",
        )

    queues = observation.get("queues", {})
    if not queues:
        return Action(action_type="hold", hold_steps=1, reason="heuristic_no_observation")

    busiest = Direction(max(queues, key=queues.get))
    opposite = _OPPOSITE[busiest]
    signal_actions = []
    for direction in Direction:
        light = LightState.GREEN if direction in {busiest, opposite} else LightState.RED
        signal_actions.append(SignalAction(direction=direction, light=light))

    return Action(action_type="set_phase", signal_actions=signal_actions, reason="heuristic_queue_balancing")


def _choose_action(client: OpenAI, model: str, observation: dict) -> Action:
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        seed=42,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Observation JSON:\n"
                    f"{json.dumps(observation, indent=2)}\n\n"
                    "Return one valid action JSON with keys matching the Action schema."
                ),
            },
        ],
    )

    raw = response.choices[0].message.content or "{}"
    try:
        return Action.model_validate(json.loads(raw))
    except Exception:
        return _heuristic_action(observation)


def run_baseline(model: str = "gpt-4.1-mini") -> dict[str, float]:
    key = os.getenv("OPENAI_API_KEY")
    api_enabled = bool(key)
    client = OpenAI(api_key=key) if api_enabled else None
    if not api_enabled:
        print("OPENAI_API_KEY not found. Running deterministic heuristic baseline.")

    env = IntersectionEnv()

    scores: dict[str, float] = {}
    for task_id in env.task_ids:
        obs = env.reset(task_id)
        done = False
        while not done:
            observation = obs.model_dump(mode="json")
            if api_enabled and client is not None:
                try:
                    action = _choose_action(client, model, observation)
                except Exception:
                    api_enabled = False
                    print("OpenAI API unavailable or key invalid. Falling back to deterministic heuristic.")
                    action = _heuristic_action(observation)
            else:
                action = _heuristic_action(observation)

            obs, _reward, done, _info = env.step(action)

        scores[task_id] = round(grade_task(env.state()).score, 4)

    scores["average"] = round(sum(scores.values()) / len(scores), 4)
    return scores
