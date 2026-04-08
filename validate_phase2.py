#!/usr/bin/env python3
"""Phase 2 Hackathon Validation - Comprehensive Test"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import importlib
import yaml

def validate_yaml(yaml_path: str):
    """Validate openenv.yaml structure and graders"""
    print(f"\n{'='*70}")
    print(f"VALIDATING: {yaml_path}")
    print(f"{'='*70}\n")
    
    manifest = yaml.safe_load(Path(yaml_path).read_text())
    
    # Check required fields
    required_fields = ["name", "entrypoint", "tasks", "deployment"]
    for field in required_fields:
        if field not in manifest:
            raise ValueError(f"Missing required field: {field}")
    
    print(f"✓ YAML structure valid")
    print(f"  Name: {manifest['name']}")
    print(f"  Entrypoint: {manifest['entrypoint']}")
    
    # Load environment
    entry_mod_path, entry_cls_name = manifest["entrypoint"].split(":")
    entry_mod = importlib.import_module(entry_mod_path.replace("/", ".").removesuffix(".py"))
    env_cls = getattr(entry_mod, entry_cls_name)
    env = env_cls()
    print(f"✓ Environment class loaded: {env_cls.__name__}")
    
    # Validate tasks
    tasks = manifest.get("tasks", [])
    if len(tasks) < 3:
        raise ValueError(f"Must have at least 3 tasks, found {len(tasks)}")
    print(f"✓ At least 3 tasks defined: {len(tasks)}")
    
    # Validate each grader
    print(f"\nValidating graders:")
    all_scores = []
    for task in tasks:
        task_id = task["id"]
        grader_ref = task.get("grader")
        
        if not grader_ref:
            raise ValueError(f"Task {task_id} has no grader defined")
        
        grader_mod_path, grader_func_name = grader_ref.split(":")
        grader_mod = importlib.import_module(grader_mod_path.replace("/", ".").removesuffix(".py"))
        grader_func = getattr(grader_mod, grader_func_name)
        
        # Reset and get state
        env.reset(task_id)
        state = env.state()
        
        # Call grader
        score = grader_func(state)
        
        # Validate score
        if not isinstance(score, (int, float)):
            raise ValueError(f"Grader {grader_func_name} returned non-numeric: {type(score)}")
        
        score_float = float(score)
        if not (0.0 < score_float < 1.0):
            raise ValueError(
                f"Grader {grader_func_name} returned out-of-range score: {score_float}. "
                f"Must be strictly between 0 and 1 (not 0.0, not 1.0)"
            )
        
        all_scores.append(score_float)
        print(f"  ✓ {task_id:30} -> {score_float:.6f}")
    
    print(f"\n{'='*70}")
    print(f"RESULT: ALL VALIDATIONS PASSED")
    print(f"{'='*70}")
    return True

if __name__ == "__main__":
    try:
        validate_yaml("openenv.yaml")
        sys.exit(0)
    except Exception as exc:
        print(f"\n{'='*70}")
        print(f"VALIDATION FAILED")
        print(f"{'='*70}")
        print(f"Error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
