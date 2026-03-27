from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class Label(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    SALES = "sales"
    HR = "hr"
    SPAM = "spam"
    OTHER = "other"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionType(str, Enum):
    CLASSIFY = "classify"
    SET_PRIORITY = "set_priority"
    DRAFT_REPLY = "draft_reply"
    ARCHIVE = "archive"
    ESCALATE = "escalate"
    NOOP = "noop"


class Email(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    label: Optional[Label] = None
    priority: Priority = Priority.MEDIUM
    archived: bool = False
    escalated_to: Optional[str] = None
    draft_reply: Optional[str] = None


class Action(BaseModel):
    action_type: ActionType
    email_id: Optional[str] = None
    label: Optional[Label] = None
    priority: Optional[Priority] = None
    message: Optional[str] = None
    team: Optional[str] = None
    reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_fields(self) -> "Action":
        needs_email = {
            ActionType.CLASSIFY,
            ActionType.SET_PRIORITY,
            ActionType.DRAFT_REPLY,
            ActionType.ARCHIVE,
            ActionType.ESCALATE,
        }

        if self.action_type in needs_email and not self.email_id:
            raise ValueError("email_id is required for this action type")

        if self.action_type == ActionType.CLASSIFY and self.label is None:
            raise ValueError("label is required for classify")

        if self.action_type == ActionType.SET_PRIORITY and self.priority is None:
            raise ValueError("priority is required for set_priority")

        if self.action_type == ActionType.DRAFT_REPLY and not self.message:
            raise ValueError("message is required for draft_reply")

        if self.action_type == ActionType.ESCALATE and not self.team:
            raise ValueError("team is required for escalate")

        return self


class Observation(BaseModel):
    task_id: str
    task_instruction: str
    step_count: int
    max_steps: int
    inbox: list[Email]
    recent_actions: list[str] = Field(default_factory=list)


class Reward(BaseModel):
    value: float
    progress_delta: float
    penalties: dict[str, float] = Field(default_factory=dict)
    components: dict[str, float] = Field(default_factory=dict)


class EnvState(BaseModel):
    task_id: str
    task_instruction: str
    step_count: int
    max_steps: int
    progress: float
    done: bool
    inbox: list[Email]
    action_history: list[dict[str, Any]]
