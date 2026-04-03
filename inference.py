from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from openai import OpenAI

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openenv_intersection.agent import IntersectionAgent
from openenv_intersection.environment import IntersectionEnv
from openenv_intersection.graders import grade_task
from openenv_intersection.models import Action


def _emit(stage: str, payload: dict[str, Any]) -> None:
    print(f"[{stage}] {json.dumps(payload, separators=(',', ':'), ensure_ascii=True)}", flush=True)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _llm_action(
    client: OpenAI,
    model_name: str,
    observation: dict[str, Any],
) -> Action:
    response = client.chat.completions.create(
        model=model_name,
        temperature=0,
        seed=42,
        timeout=5.0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You control a four-way traffic intersection. "
                    "Always return exactly one JSON action matching the Action schema. "
                    "Prioritize emergency vehicles and avoid conflicting green directions."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Observation JSON:\n"
                    f"{json.dumps(observation, indent=2)}\n\n"
                    "Return only one valid action JSON object."
                ),
            },
        ],
    )
    raw = response.choices[0].message.content or "{}"
    return Action.model_validate(json.loads(raw))


def run() -> int:
    start_ts = time.time()
    api_base_url = _require_env("API_BASE_URL")
    model_name = _require_env("MODEL_NAME")
    hf_token = _require_env("HF_TOKEN")

    client = OpenAI(base_url=api_base_url, api_key=hf_token, timeout=5.0, max_retries=0)
    env = IntersectionEnv()
    heuristic = IntersectionAgent(api_key=None)

    _emit(
        "START",
        {
            "event": "run_started",
            "model": model_name,
            "api_base_url": api_base_url,
            "tasks": env.task_ids,
        },
    )

    scores: dict[str, float] = {}
    for task_id in env.task_ids:
        observation = env.reset(task_id)
        done = False

        while not done:
            obs_dict = observation.model_dump(mode="json")
            source = "openai"

            try:
                action = _llm_action(client=client, model_name=model_name, observation=obs_dict)
            except Exception:
                action = heuristic.heuristic_action(obs_dict)
                source = "heuristic"

            observation, reward, done, info = env.step(action)
            _emit(
                "STEP",
                {
                    "task_id": task_id,
                    "step": observation.step_count,
                    "source": source,
                    "action_type": action.action_type.value,
                    "reward": reward.value,
                    "done": done,
                    "score": info.get("score", 0.0),
                },
            )

        final_score = round(grade_task(env.state()).score, 4)
        scores[task_id] = final_score

    average = round(sum(scores.values()) / max(1, len(scores)), 4)
    elapsed = round(time.time() - start_ts, 3)

    _emit(
        "END",
        {
            "event": "run_completed",
            "scores": scores,
            "average": average,
            "elapsed_seconds": elapsed,
        },
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        _emit(
            "END",
            {
                "event": "run_failed",
                "error": str(exc),
                "trace": traceback.format_exc(limit=2),
            },
        )
        raise SystemExit(1)
