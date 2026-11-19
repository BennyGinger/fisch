"""Recognize run roots and resolve selections inside processed acquisitions."""

from __future__ import annotations

from pathlib import Path

from fisch.environment import naming


def is_run_root(path: Path) -> bool:
    """
    Recognize a run by its saved settings or log directory.
    """
    return any((path / directory / settings).is_file() or (path / directory / 'logs').is_dir()
               for directory, settings in ((naming.RUN_METADATA, naming.SETTINGS),
                                            (naming.LEGACY_RUN_METADATA, naming.LEGACY_SETTINGS)))


def resolve_run_root(selected: Path) -> Path:
    """
    Use the nearest established run, or accept the selection as a fresh run.
    """
    selected = selected.expanduser().resolve()
    for candidate in (selected, *selected.parents):
        if is_run_root(candidate):
            return candidate
    return selected
