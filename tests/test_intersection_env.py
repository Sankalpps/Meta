from openenv_intersection.environment import IntersectionEnv
from openenv_intersection.models import Action, Direction, LightState, SignalAction


def test_reset_returns_valid_observation() -> None:
    env = IntersectionEnv("easy_single_ambulance")
    obs = env.reset()

    assert obs.task_id == "easy_single_ambulance"
    assert len(obs.queues) == 4
    assert obs.step_count == 0
    assert obs.max_steps > 0


def test_phase_conflict_penalty() -> None:
    env = IntersectionEnv("easy_single_ambulance")
    env.reset()

    action = Action(
        action_type="set_phase",
        signal_actions=[
            SignalAction(direction=Direction.NORTH, light=LightState.GREEN),
            SignalAction(direction=Direction.SOUTH, light=LightState.GREEN),
            SignalAction(direction=Direction.EAST, light=LightState.GREEN),
            SignalAction(direction=Direction.WEST, light=LightState.RED),
        ],
    )

    _, reward, _, info = env.step(action)
    assert reward.penalties.get("signal_conflict", 0.0) < 0
    assert 0.0 < info["score"] < 1.0


def test_emergency_preempt_improves_progress() -> None:
    env = IntersectionEnv("easy_single_ambulance")
    env.reset()

    # advance until emergency appears in easy scenario
    for _ in range(6):
        env.step(Action(action_type="hold", hold_steps=1))

    env.step(Action(action_type="preempt_emergency", target_direction=Direction.NORTH))
    for _ in range(4):
        env.step(Action(action_type="hold", hold_steps=1))

    state = env.state()
    assert any(e.crossed for e in state.emergency_vehicles)
    assert state.safety_violations == 0


def test_reward_stays_in_unit_interval() -> None:
    env = IntersectionEnv("hard_dual_emergency_wave")
    env.reset()

    # Alternate safe and conflicting phases to stress both positive/negative shaping terms.
    actions = [
        Action(action_type="hold", hold_steps=1),
        Action(
            action_type="set_phase",
            signal_actions=[
                SignalAction(direction=Direction.NORTH, light=LightState.GREEN),
                SignalAction(direction=Direction.SOUTH, light=LightState.GREEN),
                SignalAction(direction=Direction.EAST, light=LightState.GREEN),
                SignalAction(direction=Direction.WEST, light=LightState.RED),
            ],
        ),
        Action(
            action_type="set_phase",
            signal_actions=[
                SignalAction(direction=Direction.NORTH, light=LightState.RED),
                SignalAction(direction=Direction.SOUTH, light=LightState.RED),
                SignalAction(direction=Direction.EAST, light=LightState.GREEN),
                SignalAction(direction=Direction.WEST, light=LightState.GREEN),
            ],
        ),
    ]

    for i in range(12):
        _, reward, _, _ = env.step(actions[i % len(actions)])
        assert 0.0 <= reward.value <= 1.0
