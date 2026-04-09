"""Tests for the EmailParser."""

import textwrap
from pathlib import Path

import pytest

from email_organizer.parser import EmailParser


SIMPLE_EML = textwrap.dedent("""\
    From: Alice <alice@example.com>
    To: Bob <bob@example.com>
    Subject: Hello World
    Date: Tue, 01 Jan 2019 12:00:00 +0000
    Message-ID: <abc123@example.com>
    Content-Type: text/plain; charset=utf-8

    Hello Bob, how are you?
""")

MULTIPART_EML = textwrap.dedent("""\
    From: sender@example.com
    To: recipient@example.com
    Subject: Multipart Test
    Date: Wed, 02 Jan 2019 08:00:00 +0000
    MIME-Version: 1.0
    Content-Type: multipart/alternative; boundary="boundary"

    --boundary
    Content-Type: text/plain; charset=utf-8

    Plain text body
    --boundary
    Content-Type: text/html; charset=utf-8

    <h1>HTML body</h1>
    --boundary--
""")


class TestEmailParser:
    def setup_method(self):
        self.parser = EmailParser()

    def test_parse_string_subject(self):
        em = self.parser.parse_string(SIMPLE_EML)
        assert em.subject == "Hello World"

    def test_parse_string_sender(self):
        em = self.parser.parse_string(SIMPLE_EML)
        assert em.sender == "alice@example.com"

    def test_parse_string_recipients(self):
        em = self.parser.parse_string(SIMPLE_EML)
        assert "bob@example.com" in em.recipients

    def test_parse_string_date(self):
        em = self.parser.parse_string(SIMPLE_EML)
        assert em.date is not None
        assert em.date.year == 2019

    def test_parse_string_body(self):
        em = self.parser.parse_string(SIMPLE_EML)
        assert "Hello Bob" in em.body

    def test_parse_string_message_id(self):
        em = self.parser.parse_string(SIMPLE_EML)
        assert "abc123" in em.message_id

    def test_parse_file(self, tmp_path):
        eml_file = tmp_path / "test.eml"
        eml_file.write_text(SIMPLE_EML, encoding="utf-8")
        em = self.parser.parse_file(eml_file)
        assert em.subject == "Hello World"
        assert em.source_path == str(eml_file)

    def test_parse_directory(self, tmp_path):
        (tmp_path / "a.eml").write_text(SIMPLE_EML, encoding="utf-8")
        (tmp_path / "b.eml").write_text(SIMPLE_EML.replace("Hello World", "Second"), encoding="utf-8")
        (tmp_path / "not_an_email.txt").write_text("ignore me", encoding="utf-8")
        emails = self.parser.parse_directory(tmp_path)
        assert len(emails) == 2
        subjects = {e.subject for e in emails}
        assert "Hello World" in subjects
        assert "Second" in subjects

    def test_parse_multipart_prefers_plaintext(self):
        em = self.parser.parse_string(MULTIPART_EML)
        assert "Plain text body" in em.body
        assert "<h1>" not in em.body

    def test_missing_date_returns_none(self):
        raw = SIMPLE_EML.replace("Date: Tue, 01 Jan 2019 12:00:00 +0000\n", "")
        em = self.parser.parse_string(raw)
        assert em.date is None
