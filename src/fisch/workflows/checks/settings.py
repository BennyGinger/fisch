"""Compare effective processing parameters with the parameters recorded in results."""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any
from scope_io import ScopeIO
from scope_io.metadata.channel_colors import conversion_channel_labels

from fisch.environment.constant import StepName
from fisch.settings.loader import resolve_step_params
from fisch.settings.models import BGSubSettings, ConvertSettings, RegisterChannelSettings, RegisterTimeSettings, SegmentSettings, SettingsModel, TrackSettings
from fisch.tasks.registration.registration_resolver import resolve_registration_plan
from fisch.workflows.checks.models import ArtifactRecord
from fisch.workflows.definitions.registry import REGISTRY


def _payload(settings: SettingsModel) -> dict[str, Any]:
    """
    Reuse each task's metadata representation, resolving registration presets.
    """
    if isinstance(settings, (RegisterTimeSettings, RegisterChannelSettings)):
        payload = settings.to_payload_dict()
        plan = resolve_registration_plan(settings.context, settings.algorithm, settings.method)
        return {**payload, "algorithm": plan.algorithm, "method": plan.method}
    if isinstance(settings, (BGSubSettings, TrackSettings)):
        return settings.to_payload_dict()
    return settings.model_dump()


def _same(first: Any, second: Any) -> bool:
    """
    Compare metadata values with consistent JSON sequence representations.
    """
    return json.dumps(first, sort_keys=True, default=str) == json.dumps(second, sort_keys=True, default=str)


def _recorded_payload(entry: Mapping[str, Any], settings: SettingsModel) -> dict[str, Any]:
    """
    Normalize registration aliases without hiding contradictory or changed parameters.
    """
    payload = {key: value for key, value in entry.items() if key not in ("channel", "timestamp", "channel_label")}
    if isinstance(settings, (RegisterTimeSettings, RegisterChannelSettings)) and "backend" in payload:
        algorithm = payload.setdefault("algorithm", payload["backend"])
        if payload["backend"] == algorithm:
            payload.pop("backend")
    return payload


def settings_problem(record: ArtifactRecord, config: Mapping[str, Any]) -> str:
    """
    Report changed processing parameters without treating execution controls as changes.
    """
    if record.metadata is None or record.step is None or record.step not in config or record.step == StepName.EDIT_TRACK:
        return ""
    saved = record.metadata.custom_metadata.get("steps", {}).get(record.step, {})
    if not saved:
        return ""
    try:
        settings = REGISTRY[record.step].model_validate(resolve_step_params(record.step, config.get(record.step, {})))
    except (ValueError, TypeError) as error:
        return f"Cannot compare processing settings: {error}"
    channels = saved.get("channels", {})
    if isinstance(settings, SegmentSettings):
        if not channels:
            return ""
        expected = {entry.channel: entry.to_payload_dict() for entry in settings.channels}
        actual: dict[str, Any] = {}
        for entry in channels.values():
            values = _recorded_payload(entry, settings)
            label = entry.get("channel_label")
            if label is None:
                return ""
            actual[label] = {"channel": label, **values}
        differs = not _same(expected, actual)
    else:
        expected_params = _payload(settings)
        recorded = [saved["params"]] if saved.get("params") else list(channels.values())
        actual_params = [_recorded_payload(entry, settings) for entry in recorded]
        if isinstance(settings, ConvertSettings):
            _resolve_conversion_labels(record, [expected_params, *actual_params], settings.source_channel_colors)
        differs = any(not _same(expected_params, entry) for entry in actual_params)
    return "Processing settings differ from this result; rerun or keep the existing result." if differs else ""


def _resolve_conversion_labels(record: ArtifactRecord,
                               payloads: list[dict[str, Any]],
                               source_colors: list[str | None] | None,
                               ) -> None:
    """
    Compare blank/default labels by their effective source names rather than syntax.
    """
    references = record.metadata.artifact.derived_from if record.metadata is not None else None
    if not isinstance(references, list):
        return
    source = next((entry.get('artifact_path') for entry in references if entry.get('external')), None)
    if not isinstance(source, str):
        return
    try:
        reader = ScopeIO.from_path(record.path.parent / source).reader
        count = reader.channel_count
        colors = source_colors if source_colors is not None else reader.channel_colors
    except (OSError, ValueError):
        return
    for number, payload in enumerate(payloads):
        payload['channel_labels'] = conversion_channel_labels(payload.get('channel_labels'), count, colors)
        if number and record.metadata is not None:
            artifact = record.metadata.artifact
            for index, label in zip(artifact.artifact_channel_indices, artifact.channel_labels or []):
                if index < count:
                    payload['channel_labels'][index] = label
