"""Read-only results prepared before populating run controls."""

from dataclasses import dataclass, field
from pathlib import Path

from fisch.workflows.checks.locations import LocationReport
from fisch.workflows.checks.models import PreflightReport, RawInputReport, RunCompatibility


@dataclass(frozen=True)
class RunInspection:
    """Carry inspected metadata to the GUI without repeating channel reads."""

    status: RunCompatibility | None = None
    artifacts: PreflightReport | None = None
    locations: LocationReport = field(default_factory=LocationReport)
    size: int = 0
    raw: RawInputReport | None = None
    channels: dict[Path, tuple[str, ...]] = field(default_factory=dict)
    imported_names: dict[int, tuple[str, ...]] = field(default_factory=dict)
