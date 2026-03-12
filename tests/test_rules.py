"""Tests for the RulesEngine."""

import pytest

from email_organizer.models import Email, Rule
from email_organizer.rules import RulesEngine, DEFAULT_RULES


def make_email(subject="", sender="test@example.com", body="") -> Email:
    return Email(subject=subject, sender=sender, recipients=[], date=None, body=body)


class TestRulesEngine:
    def test_default_rules_loaded(self):
        engine = RulesEngine()
        assert len(engine.rules) > 0

    def test_custom_rules(self):
        rules = [Rule(name="r", category="Custom", subject_contains="custom")]
        engine = RulesEngine(rules=rules)
        assert len(engine.rules) == 1

    def test_categorize_newsletter(self):
        engine = RulesEngine()
        em = make_email(subject="Weekly Newsletter — unsubscribe")
        assert engine.categorize(em) == "Newsletters"

    def test_categorize_receipt(self):
        engine = RulesEngine()
        em = make_email(subject="Your receipt #12345")
        assert engine.categorize(em) == "Receipts"

    def test_categorize_order_confirmation(self):
        engine = RulesEngine()
        em = make_email(subject="Order Confirmation #9876")
        assert engine.categorize(em) == "Receipts"

    def test_categorize_invoice(self):
        engine = RulesEngine()
        em = make_email(subject="Invoice #001 from Acme")
        assert engine.categorize(em) == "Finance"

    def test_categorize_github_notification(self):
        engine = RulesEngine()
        em = make_email(subject="PR opened", sender="notifications@github.com")
        assert engine.categorize(em) == "Notifications"

    def test_categorize_calendar_meeting(self):
        engine = RulesEngine()
        em = make_email(subject="Team meeting on Friday")
        assert engine.categorize(em) == "Calendar"

    def test_categorize_spam(self):
        engine = RulesEngine()
        em = make_email(subject="Special offer!", body="click here to unsubscribe now")
        assert engine.categorize(em) == "Spam"

    def test_categorize_default_inbox(self):
        engine = RulesEngine()
        em = make_email(subject="Hey what's up?", sender="friend@friend.com")
        assert engine.categorize(em) == RulesEngine.DEFAULT_CATEGORY

    def test_apply_sets_label(self):
        engine = RulesEngine()
        em = make_email(subject="Your receipt #1")
        engine.apply(em)
        assert "Receipts" in em.labels

    def test_apply_all(self):
        engine = RulesEngine()
        emails = [
            make_email(subject="Invoice #1"),
            make_email(subject="Hello friend"),
        ]
        engine.apply_all(emails)
        assert "Finance" in emails[0].labels
        assert RulesEngine.DEFAULT_CATEGORY in emails[1].labels

    def test_add_rule(self):
        engine = RulesEngine(rules=[])
        engine.add_rule(Rule(name="new", category="VIP", sender_contains="boss@"))
        em = make_email(sender="boss@company.com")
        assert engine.categorize(em) == "VIP"

    def test_priority_order(self):
        """Higher-priority rule should win."""
        rules = [
            Rule(name="low", category="Low", subject_contains="deal", priority=1),
            Rule(name="high", category="High", subject_contains="deal", priority=99),
        ]
        engine = RulesEngine(rules=rules)
        em = make_email(subject="great deal")
        assert engine.categorize(em) == "High"

    def test_apply_does_not_duplicate_label(self):
        engine = RulesEngine()
        em = make_email(subject="Invoice")
        engine.apply(em)
        engine.apply(em)  # called twice
        assert em.labels.count("Finance") == 1
