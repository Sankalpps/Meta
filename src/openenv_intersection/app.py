from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .environment import IntersectionEnv
from .models import Action

app = FastAPI(title="OpenEnv 4-Way Intersection", version="0.1.0")
env = IntersectionEnv()


@app.get("/")
def index() -> dict:
    return {
        "name": "openenv-intersection-emergency",
        "api": ["/reset", "/step", "/state", "/tasks"],
        "task_count": len(env.task_ids),
    }


@app.get("/tasks")
def tasks() -> dict:
    return {"tasks": env.task_ids}


@app.post("/reset")
def reset(task_id: str = "easy_single_ambulance") -> dict:
    try:
        obs = env.reset(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return obs.model_dump(mode="json")


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
