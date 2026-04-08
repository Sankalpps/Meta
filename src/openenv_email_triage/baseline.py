from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from .environment import EmailTriageEnv
from .graders import grade_task
from .models import Action


STRICT_SCORE_EPSILON = 0.01


SYSTEM_PROMPT = (
    "You are an autonomous email triage assistant. "
    "Return exactly one JSON object for the next action. "
    "Use only these action_type values: classify, set_priority, draft_reply, archive, escalate, noop."
)


def _to_jsonable(observation: Any) -> str:
    if hasattr(observation, "model_dump"):
        return json.dumps(observation.model_dump(mode="json"), indent=2)
    return json.dumps(observation, indent=2)


def _strict_score(score: float) -> float:
    return round(min(1.0 - STRICT_SCORE_EPSILON, max(STRICT_SCORE_EPSILON, float(score))), 4)


def _choose_action(client: OpenAI, model: str, observation: Any) -> Action:
    user_prompt = (
        "Current observation:\n"
        f"{_to_jsonable(observation)}\n\n"
        "Choose the best next action to maximize final grader score. "
        "Return strict JSON only."
    )

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        seed=42,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or "{}"
    try:
        payload = json.loads(content)
        return Action.model_validate(payload)
    except Exception:
        # Safe fallback keeps the episode moving without breaking reproducibility.
        return Action(action_type="noop", reason="model_output_unparseable")


def run_baseline(model: str = "gpt-4.1-mini") -> dict[str, float]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is required for baseline inference")

    client = OpenAI(api_key=api_key)
    env = EmailTriageEnv()

    scores: dict[str, float] = {}
    for task_id in env.task_ids:
        observation = env.reset(task_id)
        done = False
        while not done:
            action = _choose_action(client, model, observation)
            observation, _reward, done, _info = env.step(action)

        final_score = grade_task(task_id, env.state()).score
        scores[task_id] = _strict_score(final_score)

    scores["average"] = round(sum(scores.values()) / len(scores), 4)
    return scores
