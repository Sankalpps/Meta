from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class LightState(str, Enum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"


class ActionType(str, Enum):
    SET_PHASE = "set_phase"
    PREEMPT_EMERGENCY = "preempt_emergency"
    HOLD = "hold"


class SignalAction(BaseModel):
    direction: Direction
    light: LightState


class EmergencyVehicle(BaseModel):
    id: str
    approach: Direction
    eta_steps: int
    waited_steps: int = 0
    crossed: bool = False


class Action(BaseModel):
    action_type: ActionType
    signal_actions: list[SignalAction] = Field(default_factory=list)
    target_direction: Optional[Direction] = None
    hold_steps: int = 1
    reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_action(self) -> "Action":
        if self.action_type == ActionType.SET_PHASE and len(self.signal_actions) != 4:
            raise ValueError("set_phase requires 4 signal_actions (one per direction)")

        if self.action_type == ActionType.PREEMPT_EMERGENCY and self.target_direction is None:
            raise ValueError("preempt_emergency requires target_direction")

        if self.hold_steps < 1 or self.hold_steps > 5:
            raise ValueError("hold_steps must be between 1 and 5")

        return self


class Observation(BaseModel):
    task_id: str
    instruction: str
    step_count: int
    max_steps: int
    queues: dict[Direction, int]
    current_signals: dict[Direction, LightState]
    emergency_vehicles: list[EmergencyVehicle]
    throughput: int
    safety_violations: int
    recent_events: list[str] = Field(default_factory=list)


class Reward(BaseModel):
    value: float
    progress_delta: float
    components: dict[str, float] = Field(default_factory=dict)
    penalties: dict[str, float] = Field(default_factory=dict)


class EnvState(BaseModel):
    task_id: str
    instruction: str
    step_count: int
    max_steps: int
    queues: dict[Direction, int]
    current_signals: dict[Direction, LightState]
    emergency_vehicles: list[EmergencyVehicle]
    throughput: int
    total_wait: int
    safety_violations: int
    done: bool
    progress: float
    history: list[dict[str, Any]]
