#!/usr/bin/env python3
"""Command-line interface for the Email Organizer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from email_organizer import EmailOrganizer


def cmd_organize(args: argparse.Namespace) -> int:
    """Organize all .eml files in the inbox directory."""
    organizer = EmailOrganizer(output_dir=args.output)
    summary = organizer.organize_directory(args.inbox)
    total = sum(summary.values())
    print(f"Organized {total} email(s) from '{args.inbox}' → '{args.output}'")
    if summary:
        print("\nCategory breakdown:")
        for category, count in sorted(summary.items(), key=lambda x: -x[1]):
            print(f"  {category:<20} {count}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print a summary report of already-organized emails."""
    organizer = EmailOrganizer(output_dir=args.output)
    summary = organizer.get_summary()
    if not summary:
        print("No emails found in the index. Run 'organize' first.")
        return 0
    total = sum(summary.values())
    print(f"Email organizer report — {total} email(s) total\n")
    print(f"{'Category':<22} {'Count':>6}")
    print("-" * 30)
    for category, count in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"{category:<22} {count:>6}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="email-organizer",
        description="Automatically organize incoming emails into categorized folders.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ---- organize ----
    p_org = sub.add_parser("organize", help="Parse and organize emails from an inbox directory.")
    p_org.add_argument("inbox", help="Directory containing .eml files to process.")
    p_org.add_argument(
        "--output",
        default="organized",
        help="Output directory for categorized emails (default: ./organized).",
    )
    p_org.set_defaults(func=cmd_organize)

    # ---- report ----
    p_rep = sub.add_parser("report", help="Show a summary of already-organized emails.")
    p_rep.add_argument(
        "--output",
        default="organized",
        help="Directory produced by 'organize' (default: ./organized).",
    )
    p_rep.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
