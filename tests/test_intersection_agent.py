from fastapi.testclient import TestClient

from openenv_intersection.agent import IntersectionAgent
from openenv_intersection.app import app
from openenv_intersection.baseline import run_baseline
from openenv_intersection.models import ActionType


def test_agent_heuristic_without_api_key() -> None:
    agent = IntersectionAgent(api_key=None)
    observation = {
        "queues": {"north": 3, "south": 2, "east": 6, "west": 1},
        "emergency_vehicles": [],
    }

    action, source = agent.choose_action(observation)
    assert source == "heuristic"
    assert action.action_type in {ActionType.SET_PHASE, ActionType.HOLD, ActionType.PREEMPT_EMERGENCY}


def test_agent_step_endpoint_returns_action() -> None:
    client = TestClient(app)

    reset = client.post("/reset?task_id=easy_single_ambulance")
    assert reset.status_code == 200

    response = client.post("/agent_step")
    assert response.status_code == 200

    payload = response.json()
    assert "action_source" in payload
    assert "action" in payload
    assert "reward" in payload
    assert "observation" in payload


def test_tasks_endpoint_contains_action_schema() -> None:
    client = TestClient(app)
    response = client.get("/tasks")

    assert response.status_code == 200
    payload = response.json()
    assert "tasks" in payload and len(payload["tasks"]) >= 3
    assert "action_schema" in payload
    assert "required_by_action_type" in payload


def test_grader_endpoint_returns_score_range() -> None:
    client = TestClient(app)
    client.post("/reset?task_id=easy_single_ambulance")
    response = client.get("/grader")

    assert response.status_code == 200
    payload = response.json()
    assert 0.0 < payload["score"] < 1.0


def test_baseline_endpoint_runs() -> None:
    client = TestClient(app)
    response = client.post("/baseline?model=gpt-4.1-mini")

    assert response.status_code == 200
    payload = response.json()
    assert "scores" in payload
    assert "average" in payload["scores"]


def test_reset_get_supported_for_validator_ping() -> None:
    client = TestClient(app)
    response = client.get("/reset?task_id=easy_single_ambulance")
    assert response.status_code == 200


def test_baseline_scores_reproducible_without_openai(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    first = run_baseline(model="gpt-4.1-mini")
    second = run_baseline(model="gpt-4.1-mini")
    assert first == second
