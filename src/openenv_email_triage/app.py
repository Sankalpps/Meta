from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .environment import EmailTriageEnv
from .models import Action

app = FastAPI(title="OpenEnv Email Triage", version="0.1.0")
env = EmailTriageEnv()


@app.get("/")
def index() -> dict:
    return {
        "name": "openenv-email-triage",
        "api": ["/reset", "/step", "/state", "/tasks"],
        "task_count": len(env.task_ids),
    }


from .tasks import load_tasks

task_configs = load_tasks()

@app.get("/tasks")
def tasks() -> dict:
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "difficulty": t.difficulty,
                "max_steps": t.max_steps,
                "instruction": t.instruction,
                "grader": f"src/openenv_email_triage/graders.py:grade_{t.difficulty}",
            }
            for t in task_configs.values()
        ]
    }


@app.post("/reset")
def reset(task_id: str = "easy_invoice_spam") -> dict:
    try:
        observation = env.reset(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return observation.model_dump(mode="json")


@app.get("/state")
def state() -> dict:
    return env.state().model_dump(mode="json")


@app.post("/step")
def step(action: Action) -> dict:
    observation, reward, done, info = env.step(action)
    return {
        "observation": observation.model_dump(mode="json"),
        "reward": reward.model_dump(mode="json"),
        "done": done,
        "info": info,
    }
