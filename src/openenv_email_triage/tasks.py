from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .models import Email, Priority


@dataclass(frozen=True)
class TaskConfig:
    id: str
    title: str
    difficulty: str
    instruction: str
    max_steps: int
    inbox: List[Email]


def load_tasks() -> Dict[str, TaskConfig]:
    return {
        "easy_invoice_spam": TaskConfig(
            id="easy_invoice_spam",
            title="Invoice + Spam Triage",
            difficulty="easy",
            instruction=(
                "Triage the inbox safely. Handle billing requests promptly and remove spam. "
                "Only archive confirmed spam."
            ),
            max_steps=10,
            inbox=[
                Email(
                    id="e1",
                    sender="promo@buyfast-now.biz",
                    subject="Claim your 90% discount now!!!",
                    body="Limited offer. Click this suspicious link immediately.",
                ),
                Email(
                    id="e2",
                    sender="ap@northstar-retail.com",
                    subject="Invoice 8812 overdue - urgent",
                    body=(
                        "We were charged twice for March. Please confirm refund status and "
                        "send corrected invoice details."
                    ),
                ),
                Email(
                    id="e3",
                    sender="events@localchamber.org",
                    subject="Community breakfast invite",
                    body="Optional networking breakfast next Friday.",
                    priority=Priority.LOW,
                ),
            ],
        ),
        "medium_ops_queue": TaskConfig(
            id="medium_ops_queue",
            title="Operations Inbox Queue",
            difficulty="medium",
            instruction=(
                "Prioritize urgent customer-impacting issues, route technical incidents, and "
                "respond to high-value commercial opportunities."
            ),
            max_steps=14,
            inbox=[
                Email(
                    id="m1",
                    sender="ops@bricklanefoods.com",
                    subject="Production dashboard timeout",
                    body="All warehouse managers report 504 errors in dashboard login.",
                ),
                Email(
                    id="m2",
                    sender="procurement@lynxindustries.com",
                    subject="Need enterprise pricing proposal",
                    body="We are evaluating vendors this week for a 250-seat contract.",
                ),
                Email(
                    id="m3",
                    sender="people@acme-internal.com",
                    subject="Policy clarification for parental leave",
                    body="Can you confirm whether unused leave carries over?",
                    priority=Priority.LOW,
                ),
                Email(
                    id="m4",
                    sender="noreply@social-feed.example",
                    subject="Your weekly digest",
                    body="New likes and comments.",
                    priority=Priority.LOW,
                ),
            ],
        ),
        "hard_risk_and_vip": TaskConfig(
            id="hard_risk_and_vip",
            title="Risk, Legal, and VIP Incident",
            difficulty="hard",
            instruction=(
                "Defend against security threats, route legal risk appropriately, and keep VIP "
                "customers informed on technical incidents without data leakage."
            ),
            max_steps=18,
            inbox=[
                Email(
                    id="h1",
                    sender="it-helpdesk@secure-update.co",
                    subject="Password reset required now",
                    body="Your mailbox will be locked in 15 minutes. Send OTP to confirm identity.",
                ),
                Email(
                    id="h2",
                    sender="legal@elmstreetclinic.org",
                    subject="Data deletion demand under contract",
                    body=(
                        "A former customer alleges we retained records beyond agreed policy. "
                        "Provide legal escalation and response timeline."
                    ),
                ),
                Email(
                    id="h3",
                    sender="cto@aurora-enterprise.com",
                    subject="P1: Mobile checkout crash for VIP launch",
                    body=(
                        "Our launch event starts in 2 hours and checkout crashes for iOS users. "
                        "Need ETA and engineering owner now."
                    ),
                ),
                Email(
                    id="h4",
                    sender="newsletter@industry-trends.example",
                    subject="Top 10 cloud patterns",
                    body="Monthly newsletter.",
                    priority=Priority.LOW,
                ),
            ],
        ),
    }
