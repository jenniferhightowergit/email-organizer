"""Storage layer: write categorized emails to on-disk folders."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .models import Email


class EmailStorage:
    """Persist categorized emails to a structured directory tree.

    Layout::

        output_dir/
            Inbox/
                <message_id>.eml
            Newsletters/
                <message_id>.eml
            ...
            index.json   ← summary of all processed emails
    """

    INDEX_FILE = "index.json"

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, email: Email, source_path: Optional[str | Path] = None) -> Path:
        """Save *email* into the folder matching its first label.

        If *source_path* is provided (and the email has one), the original
        .eml file is copied there.  Otherwise a minimal .eml stub is written.

        Returns the path of the written file.
        """
        category = email.labels[0] if email.labels else "Inbox"
        category_dir = self.output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        safe_id = self._safe_filename(email.message_id)
        dest = category_dir / f"{safe_id}.eml"

        eml_source = source_path or email.source_path
        if eml_source and Path(eml_source).exists():
            shutil.copy2(eml_source, dest)
        else:
            dest.write_text(self._to_eml_stub(email), encoding="utf-8")

        return dest

    def save_all(self, emails: List[Email]) -> Dict[str, List[Path]]:
        """Save every email in the list; return a mapping of category → [paths]."""
        result: Dict[str, List[Path]] = defaultdict(list)
        for em in emails:
            path = self.save(em)
            category = em.labels[0] if em.labels else "Inbox"
            result[category].append(path)
        return dict(result)

    def write_index(self, emails: List[Email]) -> Path:
        """Write a JSON index summarising all processed emails."""
        index_path = self.output_dir / self.INDEX_FILE
        records = []
        for em in emails:
            records.append({
                "message_id": em.message_id,
                "subject": em.subject,
                "sender": em.sender,
                "recipients": em.recipients,
                "date": em.date.isoformat() if em.date else None,
                "labels": em.labels,
                "source_path": em.source_path,
            })
        index_path.write_text(
            json.dumps({"generated": datetime.now(timezone.utc).isoformat(), "emails": records}, indent=2),
            encoding="utf-8",
        )
        return index_path

    def load_index(self) -> List[dict]:
        """Load the JSON index if it exists."""
        index_path = self.output_dir / self.INDEX_FILE
        if not index_path.exists():
            return []
        return json.loads(index_path.read_text(encoding="utf-8")).get("emails", [])

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Strip characters that are unsafe in filenames."""
        return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:120]

    @staticmethod
    def _to_eml_stub(em: Email) -> str:
        """Generate a minimal RFC-2822-like representation of an email."""
        date_str = em.date.strftime("%a, %d %b %Y %H:%M:%S +0000") if em.date else ""
        lines = [
            f"From: {em.sender}",
            f"To: {', '.join(em.recipients)}",
            f"Subject: {em.subject}",
            f"Message-ID: {em.message_id}",
            f"Date: {date_str}",
            "Content-Type: text/plain; charset=utf-8",
            "",
            em.body,
        ]
        return "\n".join(lines)
