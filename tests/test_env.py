from openenv_email_triage.environment import EmailTriageEnv
from openenv_email_triage.models import Action


def test_reset_and_state() -> None:
    env = EmailTriageEnv(task_id="easy_invoice_spam")
    obs = env.reset()
    state = env.state()

    assert obs.task_id == "easy_invoice_spam"
    assert state.task_id == "easy_invoice_spam"
    assert state.step_count == 0
    assert state.done is False


def test_easy_task_can_reach_full_score() -> None:
    env = EmailTriageEnv(task_id="easy_invoice_spam")
    env.reset()

    steps = [
        Action(action_type="classify", email_id="e1", label="spam"),
        Action(action_type="archive", email_id="e1"),
        Action(action_type="classify", email_id="e2", label="billing"),
        Action(action_type="set_priority", email_id="e2", priority="high"),
        Action(
            action_type="draft_reply",
            email_id="e2",
            message="We are reviewing your invoice and will share a corrected invoice shortly.",
        ),
    ]

    done = False
    for action in steps:
        _, _, done, info = env.step(action)

    assert done is True
    assert 0.999 <= info["score"] < 1.0


def test_invalid_email_action_gets_penalty() -> None:
    env = EmailTriageEnv(task_id="easy_invoice_spam")
    env.reset()

    _, reward, _, _ = env.step(Action(action_type="archive", email_id="missing"))

    assert reward.value < 0.0
    assert "no_target_email" in reward.penalties
