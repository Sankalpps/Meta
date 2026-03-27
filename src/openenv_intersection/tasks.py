from __future__ import annotations

from dataclasses import dataclass

from .models import Direction


@dataclass(frozen=True)
class TaskConfig:
    id: str
    title: str
    difficulty: str
    instruction: str
    max_steps: int
    base_arrival_rate: dict[Direction, int]
    arrivals_by_step: dict[int, dict[Direction, int]]
    emergency_schedule: dict[int, tuple[str, Direction, int]]


def load_tasks() -> dict[str, TaskConfig]:
    return {
        "easy_single_ambulance": TaskConfig(
            id="easy_single_ambulance",
            title="Single Ambulance Priority",
            difficulty="easy",
            instruction=(
                "Operate a four-way intersection. Keep traffic moving while prioritizing one "
                "incoming ambulance with minimal delay."
            ),
            max_steps=20,
            base_arrival_rate={
                Direction.NORTH: 1,
                Direction.SOUTH: 1,
                Direction.EAST: 1,
                Direction.WEST: 1,
            },
            arrivals_by_step={5: {Direction.NORTH: 3}, 8: {Direction.WEST: 2}},
            emergency_schedule={6: ("amb1", Direction.NORTH, 3)},
        ),
        "medium_peak_with_firetruck": TaskConfig(
            id="medium_peak_with_firetruck",
            title="Peak Hour + Firetruck",
            difficulty="medium",
            instruction=(
                "Manage peak-hour congestion and clear a firetruck route quickly without "
                "causing unsafe signal conflicts."
            ),
            max_steps=26,
            base_arrival_rate={
                Direction.NORTH: 2,
                Direction.SOUTH: 2,
                Direction.EAST: 2,
                Direction.WEST: 1,
            },
            arrivals_by_step={4: {Direction.EAST: 4}, 10: {Direction.SOUTH: 3}, 16: {Direction.WEST: 3}},
            emergency_schedule={9: ("fire1", Direction.EAST, 2)},
        ),
        "hard_dual_emergency_wave": TaskConfig(
            id="hard_dual_emergency_wave",
            title="Dual Emergency Wave",
            difficulty="hard",
            instruction=(
                "Handle two emergency vehicles from conflicting approaches during congestion. "
                "Balance fairness and throughput while keeping safety violations at zero."
            ),
            max_steps=32,
            base_arrival_rate={
                Direction.NORTH: 2,
                Direction.SOUTH: 3,
                Direction.EAST: 2,
                Direction.WEST: 2,
            },
            arrivals_by_step={
                6: {Direction.SOUTH: 5},
                11: {Direction.NORTH: 4},
                18: {Direction.EAST: 4},
                24: {Direction.WEST: 4},
            },
            emergency_schedule={10: ("amb2", Direction.NORTH, 2), 17: ("pol1", Direction.WEST, 3)},
        ),
    }
