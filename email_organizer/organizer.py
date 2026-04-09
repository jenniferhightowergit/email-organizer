"""Core orchestrator: parse → categorize → store emails."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .models import Email, Rule
from .parser import EmailParser
from .rules import RulesEngine
from .storage import EmailStorage


class EmailOrganizer:
    """High-level API for the email organizer.

    Usage::

        organizer = EmailOrganizer(output_dir="/path/to/output")
        summary = organizer.organize_directory("/path/to/inbox")
        print(summary)
    """

    def __init__(
        self,
        output_dir: str | Path,
        rules: Optional[List[Rule]] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self._parser = EmailParser()
        self._engine = RulesEngine(rules=rules)
        self._storage = EmailStorage(self.output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def organize_directory(self, inbox_dir: str | Path) -> Dict[str, int]:
        """Parse, categorize, and store all .eml files in *inbox_dir*.

        Returns a summary dict mapping category name → count of emails.
        """
        inbox_dir = Path(inbox_dir)
        emails = self._parser.parse_directory(inbox_dir)
        return self._process(emails)

    def organize_file(self, path: str | Path) -> Email:
        """Organize a single .eml file.  Returns the processed Email object."""
        email = self._parser.parse_file(path)
        self._engine.apply(email)
        self._storage.save(email)
        self._refresh_index([email])
        return email

    def organize_string(self, raw: str) -> Email:
        """Organize a raw email string.  Returns the processed Email object."""
        email = self._parser.parse_string(raw)
        self._engine.apply(email)
        self._storage.save(email)
        self._refresh_index([email])
        return email

    def add_rule(self, rule: Rule) -> None:
        """Add a custom categorization rule at runtime."""
        self._engine.add_rule(rule)

    def get_summary(self) -> Dict[str, int]:
        """Return a category → count summary from the stored index."""
        records = self._storage.load_index()
        summary: Dict[str, int] = {}
        for record in records:
            for label in record.get("labels", ["Inbox"]):
                summary[label] = summary.get(label, 0) + 1
        return summary

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _process(self, emails: List[Email]) -> Dict[str, int]:
        self._engine.apply_all(emails)
        self._storage.save_all(emails)
        self._storage.write_index(emails)
        summary: Dict[str, int] = {}
        for em in emails:
            for label in em.labels:
                summary[label] = summary.get(label, 0) + 1
        return summary

    def _refresh_index(self, new_emails: List[Email]) -> None:
        """Append new emails to the existing index."""
        existing = self._storage.load_index()
        existing_ids = {r["message_id"] for r in existing}
        all_emails = list(new_emails)  # start fresh with new ones
        # Re-hydrate existing index entries as minimal Email objects
        from .models import Email as EmailModel  # local import to avoid circular
        from datetime import datetime

        for record in existing:
            if record["message_id"] not in {e.message_id for e in all_emails}:
                date = None
                if record.get("date"):
                    try:
                        date = datetime.fromisoformat(record["date"])
                    except ValueError:
                        pass
                em = EmailModel(
                    subject=record.get("subject", ""),
                    sender=record.get("sender", ""),
                    recipients=record.get("recipients", []),
                    date=date,
                    body="",
                    message_id=record["message_id"],
                    source_path=record.get("source_path"),
                    labels=record.get("labels", []),
                )
                all_emails.append(em)
        self._storage.write_index(all_emails)
