from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from .models import Action, Direction, LightState, SignalAction

SYSTEM_PROMPT = (
    "You control a four-way traffic intersection optimizing for three goals:\n"
    "1. EMERGENCY PRIORITY: Preempt signals immediately for ambulances/firetrucks within 2 steps\n"
    "2. THROUGHPUT: Direct green lights to reduce queue sizes and vehicle wait times\n"
    "3. SAFETY: Never create conflicting signals (opposing directions cannot both be green)\n\n"
    "Strategy:\n"
    "- If emergency vehicle ETA ≤ 1 step: PREEMPT immediately (preempt_emergency action)\n"
    "- Else: SET_PHASE to balance queues (green to highest queue + opposite direction for safety)\n"
    "- Avoid RED on all directions; minimize consecutive reds to same direction\n"
    "- Return exactly one valid Action JSON with required fields."
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
            # Build detailed context for the model
            emergency_info = ""
            emergency = observation.get("emergency_vehicles", [])
            if emergency:
                urgent = [e for e in emergency if not e.get("crossed") and int(e.get("eta_steps", 99)) <= 2]
                if urgent:
                    emergency_info = f"\nURGENT: {len(urgent)} emergency vehicle(s) arriving within 2 steps: {urgent}"
            
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
                            f"{json.dumps(observation, indent=2)}"
                            f"{emergency_info}\n\n"
                            "Return ONE valid action JSON matching the Action schema. "
                            "No reasoning text, only the JSON object."
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
        """Smart heuristic: prioritize emergencies, balance queues, ensure safety."""
        emergency = observation.get("emergency_vehicles", [])
        queues = observation.get("queues", {})
        
        # Priority 1: Emergency preemption (ETA ≤ 1 step)
        urgent_emergencies = [
            ev for ev in emergency
            if not ev.get("crossed", False) and int(ev.get("eta_steps", 99)) <= 1
        ]
        if urgent_emergencies:
            # Prioritize the most urgent (minimum ETA)
            most_urgent = min(urgent_emergencies, key=lambda e: int(e.get("eta_steps", 99)))
            return Action(
                action_type="preempt_emergency",
                target_direction=most_urgent["approach"],
                reason="heuristic_emergency_preempt",
            )
        
        # Priority 2: Upcoming emergency (ETA ≤ 3)? Prepare route
        upcoming = [
            ev for ev in emergency
            if not ev.get("crossed", False) and int(ev.get("eta_steps", 99)) <= 3
        ]
        if upcoming and queues:
            next_ev = min(upcoming, key=lambda e: int(e.get("eta_steps", 99)))
            approach_dir = Direction(next_ev["approach"])
            opposite = _OPPOSITE[approach_dir]
            signal_actions = []
            for direction in Direction:
                # Green for emergency approach and opposite (safe crossing)
                light = LightState.GREEN if direction in {approach_dir, opposite} else LightState.RED
                signal_actions.append(SignalAction(direction=direction, light=light))
            return Action(
                action_type="set_phase",
                signal_actions=signal_actions,
                reason="heuristic_emergency_prep",
            )
        
        # Priority 3: Balance queues for throughput
        if not queues:
            return Action(action_type="hold", hold_steps=1, reason="heuristic_no_traffic")
        
        # Find two directions to optimize: busiest + opposite
        sorted_dirs = sorted(queues.items(), key=lambda x: x[1], reverse=True)
        busiest = Direction(sorted_dirs[0][0])
        opposite = _OPPOSITE[busiest]
        
        # Create balanced phase
        signal_actions = []
        for direction in Direction:
            light = LightState.GREEN if direction in {busiest, opposite} else LightState.RED
            signal_actions.append(SignalAction(direction=direction, light=light))
        
        return Action(
            action_type="set_phase",
            signal_actions=signal_actions,
            reason="heuristic_queue_balance",
        )
