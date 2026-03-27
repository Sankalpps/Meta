from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .agent import IntersectionAgent
from .baseline import run_baseline
from .environment import IntersectionEnv
from .graders import grade_task
from .models import Action, ActionType
from .tasks import load_tasks

app = FastAPI(title="OpenEnv 4-Way Intersection", version="0.1.0")
env = IntersectionEnv()
task_configs = load_tasks()


def _action_requirements() -> dict[str, list[str]]:
    return {
        ActionType.SET_PHASE.value: ["action_type", "signal_actions"],
        ActionType.PREEMPT_EMERGENCY.value: ["action_type", "target_direction"],
        ActionType.HOLD.value: ["action_type"],
    }


@app.get("/")
def index() -> HTMLResponse:
        html = """
        <!doctype html>
        <html>
            <head>
                <meta charset=\"utf-8\" />
                <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
                <title>OpenEnv Intersection</title>
                <style>
                    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; background: #f6f8fb; color: #111; }
                    .card { background: #fff; border-radius: 12px; padding: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.08); max-width: 900px; }
                    h1 { margin-top: 0; }
                    code { background: #eef2ff; padding: 2px 6px; border-radius: 6px; }
                    button { margin-right: 8px; padding: 8px 12px; border: 0; border-radius: 8px; background: #0f62fe; color: #fff; cursor: pointer; }
                    pre { background: #101828; color: #e5efff; padding: 12px; border-radius: 10px; overflow: auto; }
                </style>
            </head>
            <body>
                <div class=\"card\">
                    <h1>OpenEnv Multi-Agent 4-Way Intersection</h1>
                    <p>This Space runs the emergency-priority traffic environment.</p>
                    <p>API: <code>/reset</code>, <code>/step</code>, <code>/state</code>, <code>/tasks</code></p>
                    <button onclick=\"loadTasks()\">Load Tasks</button>
                    <button onclick=\"resetEasy()\">Reset Easy Task</button>
                    <button onclick=\"loadState()\">Load State</button>
                    <button onclick="runAIStep()">AI Step</button>
                    <pre id=\"out\">Click a button to query the environment.</pre>
                </div>
                <script>
                    const out = document.getElementById('out');
                    async function render(url, options) {
                        const res = await fetch(url, options);
                        const data = await res.json();
                        out.textContent = JSON.stringify(data, null, 2);
                    }
                    function loadTasks() { render('/tasks'); }
                    function resetEasy() { render('/reset?task_id=easy_single_ambulance', { method: 'POST' }); }
                    function loadState() { render('/state'); }
                    function runAIStep() { render('/agent_step?model=gpt-4.1-mini', { method: 'POST' }); }
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html)


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
            }
            for t in task_configs.values()
        ],
        "action_schema": Action.model_json_schema(),
        "required_by_action_type": _action_requirements(),
    }


@app.get("/reset")
def reset_get(task_id: str = "easy_single_ambulance") -> dict:
    return reset(task_id)


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


@app.post("/agent_step")
def agent_step(model: str = "gpt-4.1-mini") -> dict:
    observation = env.state().model_dump(mode="json")
    agent = IntersectionAgent(model=model)
    action, source = agent.choose_action(observation)
    next_obs, reward, done, info = env.step(action)

    return {
        "action_source": source,
        "action": action.model_dump(mode="json"),
        "observation": next_obs.model_dump(mode="json"),
        "reward": reward.model_dump(mode="json"),
        "done": done,
        "info": info,
    }


@app.get("/grader")
def grader() -> dict:
    result = grade_task(env.state())
    return {
        "task_id": env.state().task_id,
        "score": result.score,
        "breakdown": result.breakdown,
    }


@app.post("/baseline")
def baseline(model: str = "gpt-4.1-mini") -> dict:
    scores = run_baseline(model=model)
    return {
        "model": model,
        "scores": scores,
    }
