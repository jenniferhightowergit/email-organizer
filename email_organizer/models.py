"""Data models for the email organizer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Email:
    """Represents a single parsed email message."""

    subject: str
    sender: str
    recipients: List[str]
    date: Optional[datetime]
    body: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_path: Optional[str] = None
    labels: List[str] = field(default_factory=list)

    @property
    def sender_domain(self) -> str:
        """Extract the domain portion of the sender address."""
        if "@" in self.sender:
            return self.sender.split("@")[-1].rstrip(">").lower()
        return ""

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Email(subject={self.subject!r}, sender={self.sender!r}, "
            f"date={self.date!r}, labels={self.labels!r})"
        )


@dataclass
class Category:
    """A named category/folder that emails can be sorted into."""

    name: str
    description: str = ""

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Category):
            return NotImplemented
        return self.name == other.name


@dataclass
class Rule:
    """A categorization rule that matches emails and assigns a label."""

    name: str
    category: str
    sender_contains: Optional[str] = None
    subject_contains: Optional[str] = None
    body_contains: Optional[str] = None
    sender_domain: Optional[str] = None
    priority: int = 0  # higher number = higher priority

    def matches(self, email: Email) -> bool:
        """Return True if this rule matches the given email."""
        if self.sender_domain and self.sender_domain.lower() not in email.sender_domain:
            return False
        if self.sender_contains and self.sender_contains.lower() not in email.sender.lower():
            return False
        if self.subject_contains and self.subject_contains.lower() not in email.subject.lower():
            return False
        if self.body_contains and self.body_contains.lower() not in email.body.lower():
            return False
        # At least one condition must be set for the rule to be valid
        if not any([
            self.sender_domain,
            self.sender_contains,
            self.subject_contains,
            self.body_contains,
        ]):
            return False
        return True
