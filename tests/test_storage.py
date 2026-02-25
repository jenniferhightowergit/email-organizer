"""Tests for EmailStorage."""

import json
from pathlib import Path

import pytest

from email_organizer.models import Email
from email_organizer.storage import EmailStorage


def make_email(subject="Test", category="Inbox") -> Email:
    em = Email(
        subject=subject,
        sender="sender@example.com",
        recipients=["recipient@example.com"],
        date=None,
        body="Test body",
        message_id=f"<{subject.lower().replace(' ', '-')}@example.com>",
    )
    em.labels = [category]
    return em


class TestEmailStorage:
    def test_save_creates_category_dir(self, tmp_path):
        storage = EmailStorage(tmp_path)
        em = make_email(category="Finance")
        storage.save(em)
        assert (tmp_path / "Finance").is_dir()

    def test_save_creates_eml_file(self, tmp_path):
        storage = EmailStorage(tmp_path)
        em = make_email(subject="My Invoice", category="Finance")
        dest = storage.save(em)
        assert dest.exists()
        assert dest.parent.name == "Finance"

    def test_save_copies_source_file(self, tmp_path):
        src = tmp_path / "source.eml"
        src.write_text("From: a@b.com\n\nBody", encoding="utf-8")
        storage = EmailStorage(tmp_path / "output")
        em = make_email(category="Inbox")
        em.source_path = str(src)
        dest = storage.save(em)
        assert dest.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")

    def test_save_all_returns_dict(self, tmp_path):
        storage = EmailStorage(tmp_path)
        emails = [make_email("E1", "Finance"), make_email("E2", "Inbox")]
        result = storage.save_all(emails)
        assert "Finance" in result
        assert "Inbox" in result

    def test_write_index(self, tmp_path):
        storage = EmailStorage(tmp_path)
        em = make_email(subject="Hello", category="Inbox")
        storage.write_index([em])
        index_path = tmp_path / "index.json"
        assert index_path.exists()
        data = json.loads(index_path.read_text())
        assert len(data["emails"]) == 1
        assert data["emails"][0]["subject"] == "Hello"

    def test_load_index_empty(self, tmp_path):
        storage = EmailStorage(tmp_path)
        assert storage.load_index() == []

    def test_load_index_after_write(self, tmp_path):
        storage = EmailStorage(tmp_path)
        em = make_email(subject="Test", category="Finance")
        storage.write_index([em])
        loaded = storage.load_index()
        assert len(loaded) == 1
        assert loaded[0]["labels"] == ["Finance"]

    def test_safe_filename(self):
        assert EmailStorage._safe_filename("<msg@example.com>") == "_msg_example.com_"
        assert EmailStorage._safe_filename("clean-name.eml") == "clean-name.eml"

    def test_eml_stub_contains_subject(self, tmp_path):
        storage = EmailStorage(tmp_path)
        em = make_email(subject="Stub Test", category="Inbox")
        dest = storage.save(em)
        content = dest.read_text(encoding="utf-8")
        assert "Stub Test" in content
