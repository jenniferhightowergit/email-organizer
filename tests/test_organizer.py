"""Integration tests for EmailOrganizer."""

import textwrap
from pathlib import Path

import pytest

from email_organizer import EmailOrganizer
from email_organizer.models import Rule


INVOICE_EML = textwrap.dedent("""\
    From: billing@vendor.com
    To: user@company.com
    Subject: Invoice #1001 for services
    Date: Mon, 10 Jan 2022 09:00:00 +0000
    Message-ID: <invoice-1001@vendor.com>
    Content-Type: text/plain; charset=utf-8

    Please find your invoice attached.
""")

NEWSLETTER_EML = textwrap.dedent("""\
    From: news@newsletter.com
    To: user@company.com
    Subject: This week's newsletter — unsubscribe here
    Date: Mon, 10 Jan 2022 10:00:00 +0000
    Message-ID: <newsletter-week1@newsletter.com>
    Content-Type: text/plain; charset=utf-8

    Latest news for you.
""")

PLAIN_EML = textwrap.dedent("""\
    From: friend@friend.com
    To: user@company.com
    Subject: What's up?
    Date: Mon, 10 Jan 2022 11:00:00 +0000
    Message-ID: <hello-1@friend.com>
    Content-Type: text/plain; charset=utf-8

    Hey! How are you?
""")


@pytest.fixture
def inbox(tmp_path):
    """Create a temporary inbox directory with sample .eml files."""
    inbox_dir = tmp_path / "inbox"
    inbox_dir.mkdir()
    (inbox_dir / "invoice.eml").write_text(INVOICE_EML, encoding="utf-8")
    (inbox_dir / "newsletter.eml").write_text(NEWSLETTER_EML, encoding="utf-8")
    (inbox_dir / "plain.eml").write_text(PLAIN_EML, encoding="utf-8")
    return inbox_dir


class TestEmailOrganizerIntegration:
    def test_organize_directory_summary(self, inbox, tmp_path):
        output = tmp_path / "output"
        organizer = EmailOrganizer(output_dir=output)
        summary = organizer.organize_directory(inbox)
        assert sum(summary.values()) == 3
        assert "Finance" in summary
        assert "Newsletters" in summary
        assert "Inbox" in summary

    def test_organize_directory_creates_folders(self, inbox, tmp_path):
        output = tmp_path / "output"
        organizer = EmailOrganizer(output_dir=output)
        organizer.organize_directory(inbox)
        assert (output / "Finance").is_dir()
        assert (output / "Newsletters").is_dir()
        assert (output / "Inbox").is_dir()

    def test_organize_directory_writes_index(self, inbox, tmp_path):
        output = tmp_path / "output"
        organizer = EmailOrganizer(output_dir=output)
        organizer.organize_directory(inbox)
        assert (output / "index.json").exists()

    def test_organize_string(self, tmp_path):
        output = tmp_path / "output"
        organizer = EmailOrganizer(output_dir=output)
        em = organizer.organize_string(INVOICE_EML)
        assert "Finance" in em.labels

    def test_organize_file(self, inbox, tmp_path):
        output = tmp_path / "output"
        organizer = EmailOrganizer(output_dir=output)
        em = organizer.organize_file(inbox / "invoice.eml")
        assert "Finance" in em.labels

    def test_get_summary(self, inbox, tmp_path):
        output = tmp_path / "output"
        organizer = EmailOrganizer(output_dir=output)
        organizer.organize_directory(inbox)
        summary = organizer.get_summary()
        assert sum(summary.values()) == 3

    def test_add_custom_rule(self, tmp_path):
        output = tmp_path / "output"
        organizer = EmailOrganizer(output_dir=output)
        organizer.add_rule(Rule(name="vip", category="VIP", sender_contains="boss@"))
        em = organizer.organize_string(
            textwrap.dedent("""\
                From: boss@company.com
                To: me@me.com
                Subject: Hello
                Message-ID: <boss-msg@company.com>
                Content-Type: text/plain

                Important message.
            """)
        )
        assert "VIP" in em.labels
