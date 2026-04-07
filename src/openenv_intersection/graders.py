from __future__ import annotations

from dataclasses import dataclass

from .models import EnvState


STRICT_SCORE_EPSILON = 0.01


@dataclass(frozen=True)
class GradeResult:
    score: float
    breakdown: dict[str, float]


def _strict_unit_interval(score: float) -> float:
    return min(1.0 - STRICT_SCORE_EPSILON, max(STRICT_SCORE_EPSILON, score))


def grade_task(state: EnvState) -> GradeResult:
    crossed_emergency = sum(1 for e in state.emergency_vehicles if e.crossed)
    total_emergency = max(1, len(state.emergency_vehicles))
    emergency_wait = sum(e.waited_steps for e in state.emergency_vehicles)

    total_queued = sum(state.queues.values())
    avg_wait_norm = min(1.0, state.total_wait / max(1, state.step_count * 20))
    queue_norm = min(1.0, total_queued / 80)

    components = {
        "emergency_priority": 0.45 * (crossed_emergency / total_emergency),
        "throughput": 0.25 * min(1.0, state.throughput / max(1, state.step_count * 3)),
        "low_wait": 0.15 * (1.0 - avg_wait_norm),
        "queue_control": 0.1 * (1.0 - queue_norm),
        "safety": 0.05 if state.safety_violations == 0 else 0.0,
    }

    penalty = min(0.3, emergency_wait / 100)
    score = _strict_unit_interval(round(sum(components.values()) - penalty, 4))
    return GradeResult(score=score, breakdown=components)


def grade_easy_single_ambulance(state: EnvState) -> GradeResult:
    return grade_task(state)


def grade_medium_peak_with_firetruck(state: EnvState) -> GradeResult:
    return grade_task(state)


def grade_hard_dual_emergency_wave(state: EnvState) -> GradeResult:
    return grade_task(state)
