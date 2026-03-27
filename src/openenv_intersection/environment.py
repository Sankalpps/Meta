from __future__ import annotations

import copy
from typing import Any, Optional

from .graders import grade_task
from .models import (
    Action,
    ActionType,
    Direction,
    EmergencyVehicle,
    EnvState,
    LightState,
    Observation,
    Reward,
)
from .tasks import TaskConfig, load_tasks


class IntersectionEnv:
    def __init__(self, task_id: str = "easy_single_ambulance") -> None:
        self._tasks = load_tasks()
        if task_id not in self._tasks:
            raise ValueError(f"Unknown task_id '{task_id}'")

        self._task: TaskConfig = self._tasks[task_id]
        self._step_count = 0
        self._done = False
        self._progress = 0.0
        self._throughput = 0
        self._total_wait = 0
        self._safety_violations = 0
        self._history: list[dict[str, Any]] = []
        self._recent_events: list[str] = []
        self._queues: dict[Direction, int] = {}
        self._signals: dict[Direction, LightState] = {}
        self._emergency: list[EmergencyVehicle] = []
        self.reset(task_id)

    @property
    def task_ids(self) -> list[str]:
        return list(self._tasks.keys())

    def reset(self, task_id: Optional[str] = None) -> Observation:
        if task_id:
            if task_id not in self._tasks:
                raise ValueError(f"Unknown task_id '{task_id}'")
            self._task = self._tasks[task_id]

        self._step_count = 0
        self._done = False
        self._throughput = 0
        self._total_wait = 0
        self._safety_violations = 0
        self._history = []
        self._recent_events = []
        self._emergency = []
        self._queues = {
            Direction.NORTH: 3,
            Direction.SOUTH: 3,
            Direction.EAST: 3,
            Direction.WEST: 3,
        }
        self._signals = {
            Direction.NORTH: LightState.RED,
            Direction.SOUTH: LightState.RED,
            Direction.EAST: LightState.GREEN,
            Direction.WEST: LightState.GREEN,
        }

        self._progress = grade_task(self.state()).score
        return self._observation()

    def state(self) -> EnvState:
        return EnvState(
            task_id=self._task.id,
            instruction=self._task.instruction,
            step_count=self._step_count,
            max_steps=self._task.max_steps,
            queues=copy.deepcopy(self._queues),
            current_signals=copy.deepcopy(self._signals),
            emergency_vehicles=copy.deepcopy(self._emergency),
            throughput=self._throughput,
            total_wait=self._total_wait,
            safety_violations=self._safety_violations,
            done=self._done,
            progress=self._progress,
            history=copy.deepcopy(self._history),
        )

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict[str, Any]]:
        if self._done:
            return self._observation(), Reward(value=0.0, progress_delta=0.0), True, {
                "warning": "Episode already done. Call reset()."
            }

        self._step_count += 1
        penalties: dict[str, float] = {}
        self._recent_events = []

        action_record = action.model_dump(mode="json", exclude_none=True)
        action_record["step"] = self._step_count
        self._history.append(action_record)

        self._spawn_traffic()
        self._spawn_emergency_if_due()
        self._apply_action(action, penalties)
        moved = self._move_vehicles()
        blocked_emergency = self._update_emergency_wait()
        if blocked_emergency > 0:
            penalties["emergency_blocked"] = round(-0.06 * blocked_emergency, 4)
        self._total_wait += sum(self._queues.values()) + sum(e.waited_steps for e in self._emergency if not e.crossed)
        self._throughput += moved

        grade = grade_task(self.state())
        progress_delta = grade.score - self._progress
        self._progress = grade.score

        reward_value = progress_delta
        reward_value += 0.02 * moved
        reward_value += penalties.get("signal_conflict", 0.0)
        reward_value += penalties.get("invalid_phase", 0.0)
        reward_value += penalties.get("emergency_blocked", 0.0)

        done_reason: Optional[str] = None
        if self._step_count >= self._task.max_steps:
            self._done = True
            done_reason = "max_steps"

        all_emergency_crossed = all(e.crossed for e in self._emergency) if self._emergency else False
        if all_emergency_crossed and self._step_count > 8 and self._progress >= 0.88:
            self._done = True
            done_reason = "objective_met"
            reward_value += 0.1

        reward = Reward(
            value=round(max(-1.0, min(1.0, reward_value)), 4),
            progress_delta=round(progress_delta, 4),
            components={
                "vehicles_moved": float(moved),
                "task_score": self._progress,
            },
            penalties=penalties,
        )

        info = {
            "task_id": self._task.id,
            "difficulty": self._task.difficulty,
            "score": self._progress,
            "breakdown": grade.breakdown,
            "done_reason": done_reason,
            "events": self._recent_events,
        }
        return self._observation(), reward, self._done, info

    def _observation(self) -> Observation:
        return Observation(
            task_id=self._task.id,
            instruction=self._task.instruction,
            step_count=self._step_count,
            max_steps=self._task.max_steps,
            queues=copy.deepcopy(self._queues),
            current_signals=copy.deepcopy(self._signals),
            emergency_vehicles=copy.deepcopy(self._emergency),
            throughput=self._throughput,
            safety_violations=self._safety_violations,
            recent_events=self._recent_events[-4:],
        )

    def _spawn_traffic(self) -> None:
        for d, rate in self._task.base_arrival_rate.items():
            self._queues[d] += rate

        if self._step_count in self._task.arrivals_by_step:
            for d, extra in self._task.arrivals_by_step[self._step_count].items():
                self._queues[d] += extra
                self._recent_events.append(f"surge:{d.value}+{extra}")

    def _spawn_emergency_if_due(self) -> None:
        if self._step_count in self._task.emergency_schedule:
            vid, approach, eta = self._task.emergency_schedule[self._step_count]
            self._emergency.append(EmergencyVehicle(id=vid, approach=approach, eta_steps=eta))
            self._recent_events.append(f"emergency:{vid}@{approach.value}")

    def _apply_action(self, action: Action, penalties: dict[str, float]) -> None:
        if action.action_type == ActionType.HOLD:
            return

        if action.action_type == ActionType.PREEMPT_EMERGENCY:
            target = action.target_direction
            if target is None:
                penalties["invalid_phase"] = -0.1
                return

            opposite = self._opposite(target)
            for d in self._signals:
                self._signals[d] = LightState.RED
            self._signals[target] = LightState.GREEN
            self._signals[opposite] = LightState.GREEN
            self._recent_events.append(f"preempt:{target.value}")
            return

        if action.action_type == ActionType.SET_PHASE:
            mapping = {item.direction: item.light for item in action.signal_actions}
            if set(mapping.keys()) != {Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST}:
                penalties["invalid_phase"] = -0.1
                return

            ns_green = mapping[Direction.NORTH] == LightState.GREEN or mapping[Direction.SOUTH] == LightState.GREEN
            ew_green = mapping[Direction.EAST] == LightState.GREEN or mapping[Direction.WEST] == LightState.GREEN
            if ns_green and ew_green:
                penalties["signal_conflict"] = -0.25
                self._safety_violations += 1
                self._recent_events.append("conflict:ns_ew_green")

            self._signals = mapping

    def _move_vehicles(self) -> int:
        moved = 0
        for d, light in self._signals.items():
            if light != LightState.GREEN:
                continue
            capacity = 3
            emergency_here = [e for e in self._emergency if e.approach == d and not e.crossed and e.eta_steps <= 0]
            if emergency_here:
                emergency_here[0].crossed = True
                moved += 1
                self._recent_events.append(f"emergency_crossed:{emergency_here[0].id}")
                capacity -= 1
            normal_move = min(capacity, self._queues[d])
            self._queues[d] -= normal_move
            moved += normal_move

        return moved

    def _update_emergency_wait(self) -> int:
        for e in self._emergency:
            if e.crossed:
                continue
            if e.eta_steps > 0:
                e.eta_steps -= 1
            else:
                e.waited_steps += 1

        ready = [e for e in self._emergency if not e.crossed and e.eta_steps <= 0]
        blocked_count = 0
        for e in ready:
            if self._signals[e.approach] != LightState.GREEN:
                blocked_count += 1

        return blocked_count

    @staticmethod
    def _opposite(direction: Direction) -> Direction:
        if direction == Direction.NORTH:
            return Direction.SOUTH
        if direction == Direction.SOUTH:
            return Direction.NORTH
        if direction == Direction.EAST:
            return Direction.WEST
        return Direction.EAST
