"""Parse email files (.eml) into Email model instances."""

from __future__ import annotations

import email
import email.policy
import os
from datetime import datetime
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import List, Optional

from .models import Email


class EmailParser:
    """Parse .eml files or raw RFC-2822 email strings into Email objects."""

    def parse_file(self, path: str | Path) -> Email:
        """Parse a single .eml file from disk."""
        path = Path(path)
        raw = path.read_bytes()
        parsed = email.message_from_bytes(raw, policy=email.policy.default)
        return self._build_email(parsed, source_path=str(path))

    def parse_string(self, raw: str) -> Email:
        """Parse a raw email string."""
        parsed = email.message_from_string(raw, policy=email.policy.default)
        return self._build_email(parsed)

    def parse_directory(self, directory: str | Path) -> List[Email]:
        """Parse all .eml files found in a directory (non-recursive)."""
        directory = Path(directory)
        emails: List[Email] = []
        for entry in sorted(directory.iterdir()):
            if entry.is_file() and entry.suffix.lower() == ".eml":
                emails.append(self.parse_file(entry))
        return emails

    def _build_email(self, msg: email.message.Message, source_path: Optional[str] = None) -> Email:
        subject = msg.get("Subject", "") or ""
        raw_from = msg.get("From", "") or ""
        _, sender_addr = parseaddr(raw_from)
        sender = sender_addr if sender_addr else raw_from

        raw_to = msg.get("To", "") or ""
        recipients = [addr for _, addr in email.utils.getaddresses([raw_to]) if addr]

        date = self._parse_date(msg.get("Date", ""))
        message_id = msg.get("Message-ID", "") or ""

        body = self._extract_body(msg)

        return Email(
            subject=subject,
            sender=sender,
            recipients=recipients,
            date=date,
            body=body,
            message_id=message_id,
            source_path=source_path,
        )

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return None

    @staticmethod
    def _extract_body(msg: email.message.Message) -> str:
        """Extract plain-text body from the message (prefers text/plain)."""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = str(part.get("Content-Disposition", ""))
                if ct == "text/plain" and "attachment" not in cd:
                    try:
                        return part.get_content()
                    except Exception:
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            return payload.decode("utf-8", errors="replace")
            return ""
        try:
            return msg.get_content()
        except Exception:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                return payload.decode("utf-8", errors="replace")
            return str(msg.get_payload() or "")
