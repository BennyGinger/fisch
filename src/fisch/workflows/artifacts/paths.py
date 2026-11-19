"""FIScH-owned discovery of current, compacted and legacy image/mask paths."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast
from pathlib import Path
from fisch.environment.paths import is_internal_path
from fisch.environment import constant as cst
from fisch.environment import naming
from fisch.workflows.experiments import discover_saved_states
from fisch.workflows.definitions.inputs import configured_profile, resolve_inputs
from fisch.settings.loader import load_settings, run_settings_path
from fisch.workflows.artifacts.provenance import read_metadata


def image_for(path: str | Path) -> Path | None:
    """
    Image for.
    """
    source = Path(path).expanduser().resolve()
    if source.is_file() and source.name in cst.IMAGE_NAMES:
        return source
    directory = source if source.is_dir() else source.parent
    if source.is_file() and source.suffix.lower() in (".tif", ".tiff"):
        try:
            refs = read_metadata(source).artifact.derived_from
            if isinstance(refs, list):
                for ref in refs:
                    candidate = (directory / ref["artifact_path"]).resolve()
                    if candidate.is_file() and candidate.name in cst.IMAGE_NAMES:
                        return candidate
        except (OSError, ValueError, KeyError):
            pass
    for name in (name for current in (*reversed(cst.IMAGE_STAGE_NAMES), cst.ARRAY_NAME) for name in naming.read_names(current)):
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def first_image(directory: Path) -> Path | None:
    """
    First image.
    """
    direct = image_for(directory)
    if direct is not None:
        return direct
    folders = sorted({p.parent for name in cst.IMAGE_NAMES for p in directory.rglob(name)
                      if not is_internal_path(p, directory)})
    return image_for(folders[0]) if folders else None


def image_input_for(path: str | Path,
                    step: cst.StepName,
                    config: Mapping[str, Any] | None = None,
                    *,
                    on_fallback: Callable[[str], None] | None = None,
                    ) -> Path | None:
    """
    Prefer the configured tuner input, then an available enabled upstream image.
    """
    # The task registry is needed for tuning, not for ordinary image viewing.
    from fisch.workflows.definitions.registry import REGISTRY
    source = Path(path).expanduser().resolve()
    directory = source if source.is_dir() else source.parent
    states = [state for state in discover_saved_states(directory.parent) if state.workdir == directory]
    if not states:
        return image_for(source)
    state = states[0]
    if state.compacted:
        raise ValueError('This experiment is compacted. Rebuild its intermediate files before tuning a processing step.')
    if config is None:
        settings = next((run_settings_path(parent) for parent in (directory, *directory.parents)
                         if run_settings_path(parent).is_file()), None)
        config = load_settings(settings) if settings else {
            name: {'enabled': name in state.completed_steps} for name in cst.WORKFLOW_ORDER}
    profile = configured_profile(REGISTRY[step].profile, config)
    expected = state.artifact(profile.input_artifact)
    if expected is None or not expected.is_file():
        candidates: list[cst.ArtifactType] = [cst.ARTI_IMG_RAW]
        for previous in cst.WORKFLOW_ORDER:
            if previous == step:
                break
            if previous in cst.IMAGE_OUTPUTS and config.get(previous, {}).get('enabled', False):
                candidates.append(cast(cst.ArtifactType, cst.IMAGE_OUTPUTS[previous]))
        for kind in reversed(candidates):
            candidate = state.artifact(kind)
            if candidate is not None and candidate.is_file():
                if on_fallback is not None:
                    expected_name = {cst.ARTI_IMG_RAW: 'converted raw image',
                                     cst.ARTI_IMG_BGSUB: 'background-subtracted image',
                                     cst.ARTI_IMG_TIME: 'frame-shifted image',
                                     cst.ARTI_IMG_CHANNEL: 'channel-shifted image'}.get(profile.input_artifact, profile.input_artifact)
                    on_fallback(f'Preview uses {candidate.name}; the configured {expected_name} '
                                'is not available yet. Run upstream steps to preview the final pipeline input.')
                return candidate
    return next(iter(resolve_inputs(state, profile).values()))
