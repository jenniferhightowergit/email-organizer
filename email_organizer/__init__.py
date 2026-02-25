"""Email Organizer - automatically categorize and sort incoming emails."""

from .models import Email, Category, Rule
from .parser import EmailParser
from .rules import RulesEngine
from .organizer import EmailOrganizer
from .storage import EmailStorage

__all__ = [
    "Email",
    "Category",
    "Rule",
    "EmailParser",
    "RulesEngine",
    "EmailOrganizer",
    "EmailStorage",
]
