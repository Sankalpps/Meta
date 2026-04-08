from __future__ import annotations

import importlib
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _validate_manifest(manifest_name: str) -> None:
    manifest_path = ROOT / manifest_name
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    tasks = manifest.get("tasks", [])
    assert len(tasks) >= 3, f"{manifest_name} must define at least 3 tasks"

    entry_mod_path, entry_cls_name = manifest["entrypoint"].split(":")
    entry_mod = importlib.import_module(entry_mod_path.replace("/", ".").removesuffix(".py"))
    env_cls = getattr(entry_mod, entry_cls_name)
    env = env_cls()

    for task in tasks:
        task_id = task["id"]
        grader_ref = task.get("grader")
        assert grader_ref, f"task {task_id} in {manifest_name} is missing grader"

        grader_mod_path, grader_func_name = grader_ref.split(":")
        grader_mod = importlib.import_module(grader_mod_path.replace("/", ".").removesuffix(".py"))
        grader_func = getattr(grader_mod, grader_func_name)

        env.reset(task_id)
        score = grader_func(env.state())
        assert isinstance(score, (int, float)), (
            f"grader {grader_ref} must return a float score for validator compatibility"
        )
        assert 0.0 < float(score) < 1.0, (
            f"grader {grader_ref} returned {score}; score must be strictly inside (0, 1)"
        )


def test_openenv_yaml_phase2_requirements() -> None:
    _validate_manifest("openenv.yaml")


def test_openenv_intersection_yaml_phase2_requirements() -> None:
    _validate_manifest("openenv_intersection.yaml")
