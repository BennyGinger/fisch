"""File-level impact diagrams built from the existing preflight inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PySide6.QtWidgets import QWidget
from fisch.gui.file_preview.models import Action, PreviewFile, PreviewGroup, STEP_ORDER as _STEP_ORDER, file_title
from fisch.gui.file_preview.widget import FilePreviewWidget

from fisch.environment import constant as cst
from fisch.workflows.artifacts.branch_masks import geometry, is_branch
from fisch.workflows.checks.models import ArtifactRecord, PreflightReport


Role = Literal["input", "selected", "affected", "conflict", "planned"]
_CAPTIONS: dict[Role, str] = {
    "input": "Input / unchanged",
    "selected": "Rerun / overwrite",
    "affected": "Affected downstream",
    "conflict": "Existing conflict",
    "planned": "Included if rebuilding",
}
_ACTIONS: dict[Role, Action] = {'input': 'keep', 'selected': 'rebuild', 'affected': 'affected',
                               'conflict': 'conflict', 'planned': 'rebuild'}


@dataclass(frozen=True)
class LineageNode:
    """Describe one displayed file and its preflight impact category."""

    path: Path
    step: str | None
    role: Role
    problem: str = ""
    new_output: bool = False
    legacy: bool = False


@dataclass(frozen=True)
class FileLineage:
    """Keep recorded file relationships separate from planned rebuild outputs."""

    nodes: tuple[LineageNode, ...]
    edges: tuple[tuple[Path, Path], ...]
    geometry_edges: tuple[tuple[Path, Path], ...] = ()


@dataclass(frozen=True)
class _LineageIndex:
    """Index report paths once for all experiment diagrams."""

    records: dict[Path, ArtifactRecord]
    directories: dict[Path, dict[Path, ArtifactRecord]]
    planned: dict[Path, list[tuple[str, Path]]]
    planned_paths: set[Path]
    registration_changes: set[Path]


def _index_lineage(report: PreflightReport) -> _LineageIndex:
    """
    Resolve and group saved and proposed outputs in one pass over the report.
    """
    registration = {cst.StepName.REGISTER_CHANNEL, cst.StepName.REGISTER_TIME}
    changing = set(report.overwritten) | set(report.affected)
    records = {record.path.resolve(): record for record in report.records}
    directories: dict[Path, dict[Path, ArtifactRecord]] = {}
    planned: dict[Path, list[tuple[str, Path]]] = {}
    planned_paths: set[Path] = set()
    registration_changes: set[Path] = set()
    for path, record in records.items():
        directories.setdefault(path.parent, {})[path] = record
        if record.step in registration and record.step in changing:
            registration_changes.add(path.parent)
    for step, output in report.rebuild_outputs:
        path = output.resolve()
        planned.setdefault(path.parent, []).append((step, path))
        planned_paths.add(path)
        if step in registration:
            registration_changes.add(path.parent)
    return _LineageIndex(records, directories, planned, planned_paths, registration_changes)


def _geometry_input(record: ArtifactRecord, records: dict[Path, ArtifactRecord]) -> Path | None:
    """
    Attach manual drawings to image geometry rather than intensity processing.
    """
    stages = {cst.StepName.CONVERT, cst.StepName.REGISTER_CHANNEL, cst.StepName.REGISTER_TIME}
    candidates = [(path, candidate) for path, candidate in records.items() if candidate.step in stages]
    if not candidates:
        candidates = [(path, candidate) for path, candidate in records.items() if candidate.path.name == cst.ARRAY_NAME]
    if record.metadata is not None:
        matching = [(path, candidate) for path, candidate in candidates if candidate.metadata is not None
                    and geometry(candidate.metadata) == geometry(record.metadata)]
        if matching:
            candidates = matching
    if not candidates:
        return None
    return max(candidates, key=lambda item: _STEP_ORDER.get(item[1].step or "", -1))[0]


def _record_node(path: Path, record: ArtifactRecord, report: PreflightReport, index: _LineageIndex) -> LineageNode:
    """
    Assign impact from the report without inventing additional downstream work.
    """
    role: Role = "input"
    if record.legacy:
        role = "conflict"
    elif is_branch(path):
        if record.problem:
            role = "conflict"
        elif path.parent in index.registration_changes:
            role = "affected"
    elif record.step in report.overwritten:
        role = "selected"
    elif record.step in report.affected:
        role = "affected"
    elif record.problem:
        role = "conflict"
    elif path in index.planned_paths:
        role = "planned"
    return LineageNode(path, record.step, role, record.problem, legacy=record.legacy)


def file_lineage(report: PreflightReport, directory: Path) -> FileLineage:
    """
    Collect one experiment's files, actual recorded ancestors and rebuild outputs.
    """
    return _file_lineage(report, directory.resolve(), _index_lineage(report))


def _file_lineage(report: PreflightReport, directory: Path, index: _LineageIndex) -> FileLineage:
    """
    Follow saved ancestors using the shared run index and experiment-local candidates.
    """
    records = index.records
    pending = list(index.directories.get(directory, {}).items())
    nodes = {path: _record_node(path, record, report, index) for path, record in pending}
    edges: set[tuple[Path, Path]] = set()
    geometry_edges: set[tuple[Path, Path]] = set()
    visited: set[Path] = set()
    while pending:
        target, record = pending.pop()
        if target in visited:
            continue
        visited.add(target)
        if is_branch(record.path):
            source = _geometry_input(record, index.directories.get(target.parent, {}))
            if source is not None:
                geometry_edges.add((source, target))
                if source not in nodes:
                    nodes[source] = _record_node(source, records[source], report, index)
                    pending.append((source, records[source]))
            continue
        refs = record.metadata.artifact.derived_from if record.metadata is not None else None
        if not isinstance(refs, list):
            continue
        for ref in refs:
            relative = ref.get("artifact_path")
            if not isinstance(relative, str):
                continue
            source = (record.path.parent / relative).resolve()
            if source == target:
                continue
            edges.add((source, target))
            if source not in nodes:
                ancestor = records.get(source)
                nodes[source] = (_record_node(source, ancestor, report, index) if ancestor is not None
                                 else LineageNode(source, None, "input"))
                if ancestor is not None:
                    pending.append((source, ancestor))
    for step, path in index.planned.get(directory, ()):
        if path not in nodes:
            role: Role = "affected" if step in report.affected else "planned"
            nodes[path] = LineageNode(path, step, role, new_output=True)
    return FileLineage(tuple(nodes.values()), tuple(sorted(edges)), tuple(sorted(geometry_edges)))


def _node_caption(node: LineageNode) -> str:
    """
    Distinguish preserved older files and prospective outputs from current overwrites.
    """
    if node.legacy:
        return "Earlier-version result (preserved)"
    if node.new_output:
        return "New output if rebuilding"
    if is_branch(node.path):
        return "Review after registration" if node.role == "affected" else (
            "Geometry needs review" if node.role == "conflict" else "Unchanged / geometry only")
    return _CAPTIONS[node.role]


def _preview_group(graph: FileLineage, directory: Path) -> PreviewGroup:
    """
    Adapt recorded conflict relationships to the shared file-icon presentation.
    """
    files = []
    for node in graph.nodes:
        action: Action = ('keep' if node.legacy else 'create' if node.new_output else
                          'review' if is_branch(node.path) and node.role == 'affected' else
                          _ACTIONS[node.role])
        step = str(cst.StepName.EXTRACT) if node.step == cst.StepName.DISTANCE_PROFILE else node.step
        files.append(PreviewFile(node.path, file_title(node.path, node.step), action,
                                 _node_caption(node) + ('\n' + node.problem if node.problem else ''),
                                 stage=_STEP_ORDER.get(step or '', -1), branch=is_branch(node.path)))
    return PreviewGroup(directory, tuple(files), graph.edges, graph.geometry_edges)


def lineage_groups(report: PreflightReport) -> tuple[PreviewGroup, ...]:
    """
    Prepare the complete review diagram without rebuilding the index per experiment.
    """
    index = _index_lineage(report)
    directories = sorted(index.directories.keys() | index.planned.keys())
    return tuple(_preview_group(_file_lineage(report, directory, index), directory) for directory in directories)


class ArtifactLineageWidget(FilePreviewWidget):
    """
    Show conflict-review semantics using the same icons as other file-action reviews.
    """

    def __init__(self, report: PreflightReport, parent: QWidget | None = None, *, compact: bool = False,
                 groups: tuple[PreviewGroup, ...] | None = None,
                 ) -> None:
        """
        Preserve saved dependencies, conditional rebuilds and manual-mask review warnings.
        """
        if groups is None:
            groups = lineage_groups(report)
        if report.legacy:
            guidance = 'Earlier-version results are preserved. Rebuilding creates current-version results from the original acquisitions.'
        elif compact:
            guidance = 'Affected results are updated only if you choose rebuild before compacting; choosing keep retains them.'
        elif report.overwritten:
            guidance = ('Selected files will be overwritten. Affected downstream files are rebuilt only with '
                        '“Selected step and downstream”; “Selected step only” keeps them and can leave conflicts.')
        else:
            guidance = 'Highlighted files have conflicts or are included in the rebuild plan. Continuing without rebuilding retains existing results.'
        super().__init__(groups, guidance, parent)
