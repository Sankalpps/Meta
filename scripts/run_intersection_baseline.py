from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openenv_intersection.baseline import run_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run intersection baseline")
    parser.add_argument("--model", default="gpt-4.1-mini")
    args = parser.parse_args()

    scores = run_baseline(args.model)
    print(json.dumps(scores, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
