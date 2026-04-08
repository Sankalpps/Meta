from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from .models import EnvState, Label, Priority


STRICT_SCORE_EPSILON = 0.01


@dataclass(frozen=True)
class GradeResult:
    score: float
    breakdown: Dict[str, float]


def _strict_unit_interval(score: float) -> float:
    return min(1.0 - STRICT_SCORE_EPSILON, max(STRICT_SCORE_EPSILON, score))


def _email_map(state: EnvState):
    return {email.id: email for email in state.inbox}


def _grade_easy_result(state: EnvState) -> GradeResult:
    emails = _email_map(state)
    spam = emails["e1"]
    invoice = emails["e2"]

    checks = {
        "spam_labeled": 0.2 if spam.label == Label.SPAM else 0.0,
        "spam_archived": 0.2 if spam.archived else 0.0,
        "invoice_labeled": 0.2 if invoice.label == Label.BILLING else 0.0,
        "invoice_priority": 0.2 if invoice.priority == Priority.HIGH else 0.0,
        "invoice_reply": 0.2
        if invoice.draft_reply and "invoice" in invoice.draft_reply.lower()
        else 0.0,
    }
    return GradeResult(score=_strict_unit_interval(round(sum(checks.values()), 4)), breakdown=checks)


def _grade_medium_result(state: EnvState) -> GradeResult:
    emails = _email_map(state)
    outage = emails["m1"]
    sales = emails["m2"]
    hr = emails["m3"]
    digest = emails["m4"]

    checks = {
        "outage_labeled": 0.15 if outage.label == Label.TECHNICAL else 0.0,
        "outage_high_priority": 0.15 if outage.priority == Priority.HIGH else 0.0,
        "outage_escalated_engineering": 0.15
        if outage.escalated_to == "engineering"
        else 0.0,
        "outage_reply": 0.1
        if outage.draft_reply and "incident" in outage.draft_reply.lower()
        else 0.0,
        "sales_labeled": 0.15 if sales.label == Label.SALES else 0.0,
        "sales_reply": 0.1
        if sales.draft_reply and "proposal" in sales.draft_reply.lower()
        else 0.0,
        "hr_labeled": 0.1 if hr.label == Label.HR else 0.0,
        "digest_archived_or_spam": 0.1
        if digest.archived or digest.label == Label.SPAM
        else 0.0,
    }
    return GradeResult(score=_strict_unit_interval(round(sum(checks.values()), 4)), breakdown=checks)


def _grade_hard_result(state: EnvState) -> GradeResult:
    emails = _email_map(state)
    phish = emails["h1"]
    legal = emails["h2"]
    vip = emails["h3"]
    newsletter = emails["h4"]

    checks = {
        "phish_labeled_spam": 0.12 if phish.label == Label.SPAM else 0.0,
        "phish_escalated_security": 0.12
        if phish.escalated_to == "security"
        else 0.0,
        "phish_no_reply": 0.06 if not phish.draft_reply else 0.0,
        "legal_labeled_other": 0.1 if legal.label == Label.OTHER else 0.0,
        "legal_escalated": 0.12 if legal.escalated_to == "legal" else 0.0,
        "legal_reply_timeline": 0.1
        if legal.draft_reply and "timeline" in legal.draft_reply.lower()
        else 0.0,
        "vip_labeled_technical": 0.12 if vip.label == Label.TECHNICAL else 0.0,
        "vip_priority_high": 0.1 if vip.priority == Priority.HIGH else 0.0,
        "vip_escalated_engineering": 0.1 if vip.escalated_to == "engineering" else 0.0,
        "vip_reply_eta": 0.1
        if vip.draft_reply and ("eta" in vip.draft_reply.lower() or "owner" in vip.draft_reply.lower())
        else 0.0,
        "newsletter_archived": 0.06 if newsletter.archived else 0.0,
    }
    return GradeResult(score=_strict_unit_interval(round(sum(checks.values()), 4)), breakdown=checks)


def grade_easy(state: EnvState) -> float:
    return _grade_easy_result(state).score


def grade_medium(state: EnvState) -> float:
    return _grade_medium_result(state).score


def grade_hard(state: EnvState) -> float:
    return _grade_hard_result(state).score


def grade_task(task_id: str, state: EnvState) -> GradeResult:
    graders: Dict[str, Callable[[EnvState], GradeResult]] = {
        "easy_invoice_spam": _grade_easy_result,
        "medium_ops_queue": _grade_medium_result,
        "hard_risk_and_vip": _grade_hard_result,
    }
    return graders[task_id](state)
