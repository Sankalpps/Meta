from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from .graders import grade_task
from .models import Action, ActionType, Email, EnvState, Label, Observation, Reward
from .tasks import TaskConfig, load_tasks


class EmailTriageEnv:
    """OpenEnv-compatible email triage environment with typed I/O models."""

    def __init__(self, task_id: str = "easy_invoice_spam") -> None:
        self._tasks = load_tasks()
        if task_id not in self._tasks:
            raise ValueError(f"Unknown task_id '{task_id}'. Available: {list(self._tasks.keys())}")

        self._task: TaskConfig = self._tasks[task_id]
        self._step_count = 0
        self._done = False
        self._progress = 0.0
        self._action_history: list[dict[str, Any]] = []
        self._emails: list[Email] = []
        self.reset(task_id)

    @property
    def task_ids(self) -> list[str]:
        return list(self._tasks.keys())

    def reset(self, task_id: Optional[str] = None) -> Observation:
        if task_id is not None:
            if task_id not in self._tasks:
                raise ValueError(f"Unknown task_id '{task_id}'. Available: {list(self._tasks.keys())}")
            self._task = self._tasks[task_id]

        self._step_count = 0
        self._done = False
        self._progress = 0.0
        self._action_history = []
        self._emails = copy.deepcopy(self._task.inbox)
        self._progress = grade_task(self._task.id, self.state()).score
        return self._observation()

    def state(self) -> EnvState:
        return EnvState(
            task_id=self._task.id,
            task_instruction=self._task.instruction,
            step_count=self._step_count,
            max_steps=self._task.max_steps,
            progress=self._progress,
            done=self._done,
            inbox=copy.deepcopy(self._emails),
            action_history=copy.deepcopy(self._action_history),
        )

    def step(self, action: Action) -> tuple[Observation, Reward, bool, Dict[str, Any]]:
        if self._done:
            return self._observation(), Reward(value=0.0, progress_delta=0.0), True, {
                "warning": "Episode already completed. Call reset()."
            }

        self._step_count += 1
        penalties: dict[str, float] = {}
        action_applied = self._apply_action(action, penalties)

        grade = grade_task(self._task.id, self.state())
        progress_delta = max(-1.0, min(1.0, grade.score - self._progress))
        self._progress = grade.score

        reward_value = progress_delta
        reward_value += penalties.get("invalid_action", 0.0)
        reward_value += penalties.get("no_target_email", 0.0)
        reward_value += penalties.get("unnecessary_archive", 0.0)
        reward_value += penalties.get("noop", 0.0)

        done_reason: Optional[str] = None
        if self._progress >= 0.999:
            self._done = True
            done_reason = "objective_completed"
            reward_value += 0.15

        if self._step_count >= self._task.max_steps and not self._done:
            self._done = True
            done_reason = "max_steps_reached"
            reward_value -= 0.1

        reward = Reward(
            value=round(max(-1.0, min(1.0, reward_value)), 4),
            progress_delta=round(progress_delta, 4),
            penalties=penalties,
            components={
                "task_score": self._progress,
                "action_applied": 1.0 if action_applied else 0.0,
            },
        )

        info = {
            "task_id": self._task.id,
            "difficulty": self._task.difficulty,
            "score": self._progress,
            "breakdown": grade.breakdown,
            "done_reason": done_reason,
        }

        return self._observation(), reward, self._done, info

    def _observation(self) -> Observation:
        return Observation(
            task_id=self._task.id,
            task_instruction=self._task.instruction,
            step_count=self._step_count,
            max_steps=self._task.max_steps,
            inbox=copy.deepcopy(self._emails),
            recent_actions=[str(item) for item in self._action_history[-3:]],
        )

    def _find_email(self, email_id: str) -> Optional[Email]:
        for email in self._emails:
            if email.id == email_id:
                return email
        return None

    def _apply_action(self, action: Action, penalties: dict[str, float]) -> bool:
        record = action.model_dump(exclude_none=True)
        record["step"] = self._step_count
        self._action_history.append(record)

        if action.action_type == ActionType.NOOP:
            penalties["noop"] = -0.03
            return True

        if not action.email_id:
            penalties["invalid_action"] = -0.08
            return False

        email = self._find_email(action.email_id)
        if email is None:
            penalties["no_target_email"] = -0.08
            return False

        if action.action_type == ActionType.CLASSIFY:
            email.label = action.label
            return True

        if action.action_type == ActionType.SET_PRIORITY:
            email.priority = action.priority
            return True

        if action.action_type == ActionType.DRAFT_REPLY:
            email.draft_reply = action.message.strip()
            return True

        if action.action_type == ActionType.ARCHIVE:
            if email.label not in {None, Label.SPAM} and self._task.id == "hard_risk_and_vip":
                penalties["unnecessary_archive"] = -0.05
            email.archived = True
            return True

        if action.action_type == ActionType.ESCALATE:
            email.escalated_to = action.team
            return True

        penalties["invalid_action"] = -0.08
        return False
