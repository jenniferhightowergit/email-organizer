"""Tests for email data models."""

import pytest
from email_organizer.models import Email, Category, Rule


class TestEmail:
    def test_sender_domain_simple(self):
        em = Email(subject="Hi", sender="alice@example.com", recipients=[], date=None, body="")
        assert em.sender_domain == "example.com"

    def test_sender_domain_with_display_name(self):
        em = Email(subject="Hi", sender="alice@github.com", recipients=[], date=None, body="")
        assert em.sender_domain == "github.com"

    def test_sender_domain_no_at(self):
        em = Email(subject="Hi", sender="unknown", recipients=[], date=None, body="")
        assert em.sender_domain == ""

    def test_labels_default_empty(self):
        em = Email(subject="S", sender="s@s.com", recipients=[], date=None, body="")
        assert em.labels == []

    def test_message_id_auto_generated(self):
        em1 = Email(subject="A", sender="a@a.com", recipients=[], date=None, body="")
        em2 = Email(subject="B", sender="b@b.com", recipients=[], date=None, body="")
        assert em1.message_id != em2.message_id


class TestCategory:
    def test_equality(self):
        c1 = Category("Inbox")
        c2 = Category("Inbox")
        assert c1 == c2

    def test_inequality(self):
        assert Category("Inbox") != Category("Spam")

    def test_hash_equal(self):
        assert hash(Category("Finance")) == hash(Category("Finance"))

    def test_hash_set(self):
        cats = {Category("Inbox"), Category("Inbox"), Category("Spam")}
        assert len(cats) == 2


class TestRule:
    def test_matches_subject_contains(self):
        rule = Rule(name="r", category="Newsletters", subject_contains="newsletter")
        em = Email(subject="Weekly Newsletter", sender="n@news.com", recipients=[], date=None, body="")
        assert rule.matches(em)

    def test_no_match_subject(self):
        rule = Rule(name="r", category="Newsletters", subject_contains="newsletter")
        em = Email(subject="Hello there", sender="x@x.com", recipients=[], date=None, body="")
        assert not rule.matches(em)

    def test_matches_sender_domain(self):
        rule = Rule(name="r", category="Notifications", sender_domain="github.com")
        em = Email(subject="PR opened", sender="notifications@github.com", recipients=[], date=None, body="")
        assert rule.matches(em)

    def test_no_match_sender_domain(self):
        rule = Rule(name="r", category="Notifications", sender_domain="github.com")
        em = Email(subject="Hi", sender="alice@example.com", recipients=[], date=None, body="")
        assert not rule.matches(em)

    def test_matches_body_contains(self):
        rule = Rule(name="r", category="Spam", body_contains="click here to unsubscribe")
        em = Email(subject="Deal", sender="s@spam.com", recipients=[], date=None, body="click here to unsubscribe now")
        assert rule.matches(em)

    def test_matches_sender_contains(self):
        rule = Rule(name="r", category="Finance", sender_contains="billing@")
        em = Email(subject="Invoice", sender="billing@example.com", recipients=[], date=None, body="")
        assert rule.matches(em)

    def test_empty_rule_never_matches(self):
        rule = Rule(name="r", category="X")
        em = Email(subject="Hi", sender="a@b.com", recipients=[], date=None, body="hello")
        assert not rule.matches(em)

    def test_all_conditions_must_pass(self):
        rule = Rule(
            name="r",
            category="Finance",
            sender_domain="bank.com",
            subject_contains="invoice",
        )
        # Wrong domain
        em = Email(subject="invoice", sender="a@other.com", recipients=[], date=None, body="")
        assert not rule.matches(em)
        # Both correct
        em2 = Email(subject="Your invoice", sender="a@bank.com", recipients=[], date=None, body="")
        assert rule.matches(em2)
