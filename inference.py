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


STRICT_SCORE_EPSILON = 0.0001


def _emit(stage: str, payload: dict[str, Any]) -> None:
    try:
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    except Exception:
        # Keep log emission resilient even if payload contains unexpected values.
        body = json.dumps({"event": "log_serialize_failed", "payload": str(payload)}, ensure_ascii=True)
    print(f"[{stage}] {body}", flush=True)


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _strict_score(score: float) -> float:
    return round(min(1.0 - STRICT_SCORE_EPSILON, max(STRICT_SCORE_EPSILON, float(score))), 4)


def _build_openai_client() -> tuple[OpenAI | None, str, str, list[str]]:
    api_base_url = _optional_env("API_BASE_URL")
    model_name = _optional_env("MODEL_NAME") or "gpt-4.1-mini"
    hf_token = _optional_env("HF_TOKEN")
    warnings: list[str] = []

    if not api_base_url:
        warnings.append("missing_api_base_url")
    if not hf_token:
        warnings.append("missing_hf_token")

    if warnings:
        return None, "", model_name, warnings

    try:
        client = OpenAI(base_url=api_base_url, api_key=hf_token, timeout=2.0, max_retries=0)
        return client, api_base_url, model_name, []
    except Exception as exc:
        return None, api_base_url, model_name, [f"openai_client_init_failed:{type(exc).__name__}"]


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
    client, api_base_url, model_name, startup_warnings = _build_openai_client()
    env = IntersectionEnv()
    heuristic = IntersectionAgent(api_key=None)

    _emit(
        "START",
        {
            "event": "run_started",
            "model": model_name,
            "api_base_url": api_base_url or "",
            "policy_mode": "openai_with_fallback" if client is not None else "heuristic_only",
            "warnings": startup_warnings,
            "tasks": env.task_ids,
        },
    )

    scores: dict[str, float] = {}
    openai_disabled = client is None
    openai_failures = 0

    for task_id in env.task_ids:
        try:
            observation = env.reset(task_id)
        except Exception as exc:
            _emit(
                "STEP",
                {
                    "task_id": task_id,
                    "event": "task_reset_failed",
                    "error": f"{type(exc).__name__}:{exc}",
                },
            )
            scores[task_id] = _strict_score(0.0)
            continue

        done = False
        fallback_count = 0
        step_errors = 0

        while not done:
            obs_dict = observation.model_dump(mode="json")
            source = "openai" if not openai_disabled else "heuristic"

            try:
                if openai_disabled or client is None:
                    raise RuntimeError("openai_disabled")
                action = _llm_action(client=client, model_name=model_name, observation=obs_dict)
            except Exception:
                action = heuristic.heuristic_action(obs_dict)
                source = "heuristic"
                fallback_count += 1
                if not openai_disabled:
                    openai_failures += 1
                    if openai_failures >= 1:
                        openai_disabled = True
                        _emit(
                            "STEP",
                            {
                                "task_id": task_id,
                                "event": "openai_disabled_after_failure",
                                "openai_failures": openai_failures,
                            },
                        )

            try:
                observation, reward, done, info = env.step(action)
            except Exception as exc:
                step_errors += 1
                _emit(
                    "STEP",
                    {
                        "task_id": task_id,
                        "event": "task_step_failed",
                        "error": f"{type(exc).__name__}:{exc}",
                        "step_errors": step_errors,
                    },
                )
                done = True
                break

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
                    "fallback_count": fallback_count,
                    "openai_disabled": openai_disabled,
                },
            )

        try:
            final_score = _strict_score(grade_task(env.state()).score)
        except Exception as exc:
            _emit(
                "STEP",
                {
                    "task_id": task_id,
                    "event": "task_grade_failed",
                    "error": f"{type(exc).__name__}:{exc}",
                },
            )
            final_score = _strict_score(0.0)
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
    exit_code = 0
    try:
        exit_code = run()
    except Exception as exc:
        _emit(
            "END",
            {
                "event": "run_failed",
                "error": str(exc),
                "trace": traceback.format_exc(limit=2),
            },
        )
        exit_code = 0
    raise SystemExit(exit_code)
