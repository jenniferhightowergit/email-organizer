"""Rules engine: apply categorization rules to emails."""

from __future__ import annotations

from typing import List, Optional

from .models import Email, Rule


# Built-in default rules (can be extended or replaced)
DEFAULT_RULES: List[Rule] = [
    Rule(
        name="newsletters",
        category="Newsletters",
        subject_contains="unsubscribe",
        priority=10,
    ),
    Rule(
        name="newsletters_list",
        category="Newsletters",
        subject_contains="newsletter",
        priority=10,
    ),
    Rule(
        name="receipts",
        category="Receipts",
        subject_contains="receipt",
        priority=20,
    ),
    Rule(
        name="orders",
        category="Receipts",
        subject_contains="order confirmation",
        priority=20,
    ),
    Rule(
        name="invoices",
        category="Finance",
        subject_contains="invoice",
        priority=20,
    ),
    Rule(
        name="payment",
        category="Finance",
        subject_contains="payment",
        priority=15,
    ),
    Rule(
        name="github_notifications",
        category="Notifications",
        sender_domain="github.com",
        priority=5,
    ),
    Rule(
        name="calendar_invites",
        category="Calendar",
        subject_contains="invitation",
        priority=10,
    ),
    Rule(
        name="meeting_requests",
        category="Calendar",
        subject_contains="meeting",
        priority=10,
    ),
    Rule(
        name="spam_unsubscribe",
        category="Spam",
        body_contains="click here to unsubscribe",
        priority=30,
    ),
    Rule(
        name="promotions",
        category="Promotions",
        subject_contains="% off",
        priority=5,
    ),
    Rule(
        name="promotions_deal",
        category="Promotions",
        subject_contains="deal",
        priority=5,
    ),
    Rule(
        name="promotions_sale",
        category="Promotions",
        subject_contains="sale",
        priority=5,
    ),
]


class RulesEngine:
    """Apply a list of Rules to Email objects to assign category labels."""

    DEFAULT_CATEGORY = "Inbox"

    def __init__(self, rules: Optional[List[Rule]] = None) -> None:
        # Sort rules by descending priority so highest-priority rules are checked first
        self._rules: List[Rule] = sorted(
            rules if rules is not None else DEFAULT_RULES,
            key=lambda r: r.priority,
            reverse=True,
        )

    @property
    def rules(self) -> List[Rule]:
        return list(self._rules)

    def add_rule(self, rule: Rule) -> None:
        """Add a rule and re-sort by priority."""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def categorize(self, email: Email) -> str:
        """Return the category name for *email* based on matching rules.

        Applies the highest-priority matching rule. Falls back to
        ``DEFAULT_CATEGORY`` if no rule matches.
        """
        for rule in self._rules:
            if rule.matches(email):
                return rule.category
        return self.DEFAULT_CATEGORY

    def apply(self, email: Email) -> Email:
        """Assign labels in-place and return the email."""
        category = self.categorize(email)
        if category not in email.labels:
            email.labels.append(category)
        return email

    def apply_all(self, emails: List[Email]) -> List[Email]:
        """Apply rules to every email in the list."""
        return [self.apply(e) for e in emails]
