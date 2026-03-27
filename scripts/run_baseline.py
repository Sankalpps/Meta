from __future__ import annotations

import argparse
import json

from openenv_email_triage.baseline import run_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpenEnv baseline across all tasks")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model id")
    args = parser.parse_args()

    scores = run_baseline(model=args.model)
    print(json.dumps(scores, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
