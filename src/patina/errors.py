"""User-facing errors."""

from __future__ import annotations


class PatinaError(Exception):
    """An expected failure, reported to the user as a single line (exit code 1)."""
