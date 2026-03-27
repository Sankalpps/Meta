from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

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


class IntersectionAgent:
    """Policy wrapper that uses OpenAI when available and falls back to a deterministic heuristic."""

    def __init__(self, model: str = "gpt-4.1-mini", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self._client = OpenAI(api_key=self.api_key) if self.api_key else None

    @property
    def uses_openai(self) -> bool:
        return self._client is not None

    def choose_action(self, observation: dict[str, Any]) -> tuple[Action, str]:
        if self._client is None:
            return self.heuristic_action(observation), "heuristic"

        try:
            response = self._client.chat.completions.create(
                model=self.model,
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
            return Action.model_validate(json.loads(raw)), "openai"
        except Exception:
            return self.heuristic_action(observation), "heuristic"

    @staticmethod
    def heuristic_action(observation: dict[str, Any]) -> Action:
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
