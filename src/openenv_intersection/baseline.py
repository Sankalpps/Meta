from __future__ import annotations

from .agent import IntersectionAgent
from .environment import IntersectionEnv
from .graders import grade_task


def run_baseline(model: str = "gpt-4.1-mini") -> dict[str, float]:
    agent = IntersectionAgent(model=model)
    if not agent.uses_openai:
        print("OPENAI_API_KEY not found. Running deterministic heuristic baseline.")

    env = IntersectionEnv()

    scores: dict[str, float] = {}
    for task_id in env.task_ids:
        obs = env.reset(task_id)
        done = False
        while not done:
            observation = obs.model_dump(mode="json")
            action, source = agent.choose_action(observation)
            if source == "heuristic" and agent.uses_openai:
                print("OpenAI API unavailable or key invalid. Falling back to deterministic heuristic.")

            obs, _reward, done, _info = env.step(action)

        scores[task_id] = round(grade_task(env.state()).score, 4)

    scores["average"] = round(sum(scores.values()) / len(scores), 4)
    return scores
