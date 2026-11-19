"""Validate imported channel suggestions and Convert-only label updates."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
import shutil
from time import monotonic, sleep

import numpy as np
import pandas as pd
import pytest
import tifffile
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from scope_io import ScopeIO

from fisch.channel_labels import apply_labels, files_to_update
from fisch.channel_labels.conversion import prepare_conversion_labels
from fisch.environment import constant as cst
from fisch.gui.main_window.window import FischMainWindow
from fisch.gui.settings import SettingsAdapter
from fisch.gui.settings.conversion_channels import ConversionChannelsWidget
from fisch.gui.theme import get_application
from fisch.gui.viewer.registration.window import RegistrationTunerWindow
from fisch.gui.viewer.segmentation.window import SegmentationTunerWindow
from fisch.pipeline import start_pipeline
from fisch.settings.models import RegisterTimeSettings, SegmentSettings
from fisch.tasks.common.table_results import save_parquet
from fisch.workflows.checks.artifacts import inspect_run
from fisch.workflows.checks.compatibility import require_current_source
from fisch.workflows.experiments import ExperimentState, discover_saved_states
from fisch.workflows.experiments.conversion import imported_channel_names
from fisch.workflows.definitions.inputs import configured_profile, resolve_inputs
from fisch.workflows.definitions.registry import REGISTRY


def _processed(root: Path, name: str, labels: list[str]) -> ExperimentState:
    """
    Produce a real converted acquisition, then import its portable folder.
    """
    source = root.parent / (name + '_source')
    source.mkdir()
    count = max(len(labels), 1)
    pixels = np.arange(64 * count, dtype=np.uint16).reshape(count, 8, 8)
    tifffile.imwrite(source / f'{name}.tif', pixels.squeeze(axis=0) if count == 1 else pixels,
                     imagej=True, metadata={'axes': 'YX' if count == 1 else 'CYX'})
    adapter = SettingsAdapter()
    adapter.run_dir, adapter.user_name = str(source), 'Test'
    adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', labels)
    start_pipeline(adapter.save_to_run_dir(), terminal_progress=False)
    state = discover_saved_states(source)[0]
    root.mkdir(exist_ok=True)
    shutil.move(state.original_image.parent, root / name)
    return next(state for state in discover_saved_states(root) if state.original_image.stem == name)


@pytest.fixture
def imported_window(tmp_path: Path) -> Iterator[tuple[FischMainWindow, ExperimentState]]:
    """
    Open a fresh run containing one processed acquisition and one fresh input.
    """
    app = get_application()
    root = tmp_path / 'combined'
    state = _processed(root, 'old', ['GFP'])
    tifffile.imwrite(root / 'fresh.tif', np.ones((8, 8), dtype=np.uint16), photometric='minisblack')
    adapter = SettingsAdapter()
    adapter.run_dir, adapter.user_name = str(root), 'Test'
    window = FischMainWindow(adapter)
    window.show()
    app.processEvents()
    yield window, state
    window.close()
    window.deleteLater()
    app.processEvents()


def test_mixed_run_starts_in_convert_with_display_only_hints(imported_window: tuple[FischMainWindow, ExperimentState]) -> None:
    """
    One converted acquisition does not skip Convert or confirm imported names.
    """
    window, _ = imported_window
    assert window._current_step == cst.StepName.CONVERT
    assert 'GFP?' in window.file_channels_label.text()
    widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
    assert isinstance(widget, ConversionChannelsWidget)
    assert widget.value() == []
    item = widget.table.item(0, 2)
    assert item is not None and item.text() == ''
    assert item.data(Qt.ItemDataRole.UserRole) == 'GFP?'
    assert not (Path(window.adapter.run_dir) / '.pipeline/settings.toml').exists()


@pytest.mark.parametrize('requested, expected', [(['GFP'], 'GFP'), (['New'], 'New'), ([], 'C1')])
def test_next_relabels_before_launching_fresh_conversion(imported_window: tuple[FischMainWindow, ExperimentState],
                                                       monkeypatch: pytest.MonkeyPatch,
                                                       requested: list[str], expected: str,
                                                       ) -> None:
    """
    Confirm, replace, or clear labels before conversion starts, preserving pixels.
    """
    window, state = imported_window
    artifact = state.artifact(cst.ARTI_IMG_RAW)
    assert artifact is not None
    before = artifact.read_bytes()
    original_before = state.original_image.read_bytes()
    table = state.workdir / cst.QUANTI_NAME
    save_parquet(pd.DataFrame({'object_channel': ['GFP'], 'intensity_channel': ['GFP']}), table,
                 ScopeIO.from_path(artifact).metadata.with_artifact(artifact_type=cst.ARTI_QUANTI))
    launched: list[bool] = []

    def launch(*, convert_only: bool) -> None:
        """
        Verify relabeling completed before fresh conversion was requested.
        """
        assert ScopeIO.from_path(artifact).channel_labels == [expected]
        assert pd.read_parquet(table).loc[0, 'object_channel'] == expected
        launched.append(convert_only)

    monkeypatch.setattr(window, '_launch_pipeline', launch)
    widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
    assert isinstance(widget, ConversionChannelsWidget)
    widget.set_labels(requested)
    window.adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', requested)
    window._next_from_convert()
    assert launched == [True], window.console.toPlainText()
    assert state.original_image.read_bytes() == original_before
    np.testing.assert_array_equal(tifffile.imread(artifact).squeeze(), np.arange(64, dtype=np.uint16).reshape(8, 8))
    if expected == 'GFP':
        assert artifact.read_bytes() == before
    else:
        assert 'WARNING | Channel labels updated' in window.console.toPlainText()
    names = imported_channel_names(discover_saved_states(Path(window.adapter.run_dir)))
    assert names == {0: (expected,)}


def test_mixed_labels_are_suggestions_and_can_be_unified(tmp_path: Path) -> None:
    """
    Mixed portable names are handled by per-acquisition mappings in one update.
    """
    root = tmp_path / 'combined'
    first = _processed(root, 'first', ['GFP'])
    second = _processed(root, 'second', ['Other'])
    assert imported_channel_names([first, second]) == {0: ('GFP', 'Other')}
    update = prepare_conversion_labels(root, ['Unified'])
    assert update is not None and update.acquisition_count == 2
    apply_labels(update.plan, update.proposed)
    for state in (first, second):
        path = state.artifact(cst.ARTI_IMG_RAW)
        assert path is not None
        assert ScopeIO.from_path(path).channel_labels == ['Unified']
    adapter = SettingsAdapter()
    adapter.run_dir = str(root)
    adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', ['Unified'])
    assert not inspect_run(root, adapter.as_mapping(), for_execution=False).conflicts


def test_failed_combined_relabel_restores_every_acquisition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Failure in a later acquisition restores all earlier changed files.
    """
    root = tmp_path / 'combined'
    _processed(root, 'first', ['GFP'])
    _processed(root, 'second', ['Other'])
    update = prepare_conversion_labels(root, ['Unified'])
    assert update is not None
    before = {path: path.read_bytes() for path in files_to_update(update.plan, update.proposed)}
    original: Callable[..., Any] = ScopeIO.set_channel_labels
    calls = 0

    def fail_second(reader: ScopeIO, *args: Any, **kwargs: Any) -> None:
        """
        Fail after the first image has already been updated.
        """
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('simulated write failure')
        original(reader, *args, **kwargs)

    monkeypatch.setattr(ScopeIO, 'set_channel_labels', fail_second)
    with pytest.raises(RuntimeError, match='simulated write failure'):
        apply_labels(update.plan, update.proposed)
    assert all(path.read_bytes() == data for path, data in before.items())


def test_mixed_names_follow_source_indices_in_each_acquisition(tmp_path: Path) -> None:
    """
    Resolve reused names independently when imports label channel positions differently.
    """
    root = tmp_path / 'combined'
    first = _processed(root, 'first', ['GFP', 'RFP'])
    second = _processed(root, 'second', ['RFP', 'GFP'])
    for state in (first, second):
        path = state.artifact(cst.ARTI_IMG_RAW)
        assert path is not None
        save_parquet(pd.DataFrame({'object_channel': ['GFP']}), state.workdir / cst.QUANTI_NAME,
                     ScopeIO.from_path(path).metadata.with_artifact(artifact_type=cst.ARTI_QUANTI))
    update = prepare_conversion_labels(root, ['Green', 'Red'])
    assert update is not None
    apply_labels(update.plan, update.proposed)
    assert pd.read_parquet(first.workdir / cst.QUANTI_NAME).loc[0, 'object_channel'] == 'Green'
    assert pd.read_parquet(second.workdir / cst.QUANTI_NAME).loc[0, 'object_channel'] == 'Red'
    for state in (first, second):
        path = state.artifact(cst.ARTI_IMG_RAW)
        assert path is not None
        assert ScopeIO.from_path(path).channel_labels == ['Green', 'Red']


def test_ambiguous_master_names_block_before_writing(tmp_path: Path) -> None:
    """
    Do not guess which source index a mixed combined-table label represents.
    """
    root = tmp_path / 'combined'
    first = _processed(root, 'first', ['GFP', 'RFP'])
    _processed(root, 'second', ['RFP', 'GFP'])
    pd.DataFrame({'object_channel': ['GFP']}).to_parquet(root / 'master_quantification.parquet')
    path = first.artifact(cst.ARTI_IMG_RAW)
    assert path is not None
    before = path.read_bytes()
    with pytest.raises(ValueError, match='ambiguous imported channel names'):
        prepare_conversion_labels(root, ['Green', 'Red'])
    assert path.read_bytes() == before


def test_fresh_only_has_no_suggestions(tmp_path: Path) -> None:
    """
    Keep reader/default labels separate from imported-name suggestions.
    """
    app = get_application()
    tifffile.imwrite(tmp_path / 'fresh.tif', np.ones((8, 8), dtype=np.uint16), photometric='minisblack')
    adapter = SettingsAdapter()
    adapter.run_dir = str(tmp_path)
    window = FischMainWindow(adapter)
    try:
        widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
        assert isinstance(widget, ConversionChannelsWidget)
        assert window._current_step == cst.StepName.CONVERT
        item = widget.table.item(0, 2)
        assert item is not None and not item.data(Qt.ItemDataRole.UserRole)
        assert '?' not in window.file_channels_label.text()
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()


def test_mixed_label_hints_are_visible(imported_window: tuple[FischMainWindow, ExperimentState]) -> None:
    """
    Display disagreement explicitly rather than selecting one imported name.
    """
    window, _ = imported_window
    _processed(Path(window.adapter.run_dir), 'other', ['Other'])
    window._refresh_run_inventory()
    assert 'Mixed?' in window.file_channels_label.text()
    widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
    assert isinstance(widget, ConversionChannelsWidget)
    item = widget.table.item(0, 2)
    assert item is not None and item.data(Qt.ItemDataRole.UserRole) == 'Mixed?'
    assert 'GFP' in item.toolTip() and 'Other' in item.toolTip()


def test_return_to_convert_changes_existing_labels_without_reconversion(imported_window: tuple[FischMainWindow, ExperimentState],
                                                                      monkeypatch: pytest.MonkeyPatch,
                                                                      ) -> None:
    """
    Reuse Next for label-only updates in a fully converted run.
    """
    window, state = imported_window
    (Path(window.adapter.run_dir) / 'fresh.tif').unlink()
    window._refresh_run_inventory()
    widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
    assert isinstance(widget, ConversionChannelsWidget)
    widget.set_labels(['New'])
    window.adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', ['New'])
    launched: list[bool] = []
    monkeypatch.setattr(window, '_launch_pipeline', lambda **kwargs: launched.append(True))
    window._next_from_convert()
    assert not launched
    path = state.artifact(cst.ARTI_IMG_RAW)
    assert path is not None and ScopeIO.from_path(path).channel_labels == ['New']
    assert window._current_step == cst.StepName.REGISTER_TIME


def test_relabel_failure_does_not_start_conversion(imported_window: tuple[FischMainWindow, ExperimentState],
                                                 monkeypatch: pytest.MonkeyPatch,
                                                 ) -> None:
    """
    Report a failed update in red and leave fresh conversion unstarted.
    """
    window, _ = imported_window
    widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
    assert isinstance(widget, ConversionChannelsWidget)
    widget.set_labels(['New'])
    window.adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', ['New'])

    def fail(*args: Any, **kwargs: Any) -> None:
        """
        Simulate a write failure in the shared rename operation.
        """
        raise OSError('cannot update labels')

    launched: list[bool] = []
    monkeypatch.setattr('fisch.gui.main_window.window.apply_labels', fail)
    monkeypatch.setattr(window, '_launch_pipeline', lambda **kwargs: launched.append(True))
    window._next_from_convert()
    assert not launched
    assert 'conversion has not started' in window.console.toPlainText()


def test_save_and_run_pipeline_do_not_relabel(imported_window: tuple[FischMainWindow, ExperimentState],
                                             monkeypatch: pytest.MonkeyPatch,
                                             ) -> None:
    """
    Keep the label-edit operation exclusive to Convert's Next action.
    """
    window, state = imported_window
    widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
    assert isinstance(widget, ConversionChannelsWidget)
    widget.set_labels(['New'])
    window.adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', ['New'])
    assert window._save_settings() is not None
    path = state.artifact(cst.ARTI_IMG_RAW)
    assert path is not None and ScopeIO.from_path(path).channel_labels == ['GFP']
    window._show_step(cst.StepName.REGISTER_TIME)
    launched: list[bool] = []

    def launch(*, convert_only: bool) -> None:
        """
        Observe the normal pipeline launch without writing artifacts.
        """
        launched.append(convert_only)

    monkeypatch.setattr(window, '_launch_pipeline', launch)
    window._run_pipeline()
    assert launched == [False]
    assert ScopeIO.from_path(path).channel_labels == ['GFP']


@pytest.mark.parametrize('action', ['next', 'pipeline'])
def test_real_gui_launch_skips_matching_portable_conversion(imported_window: tuple[FischMainWindow, ExperimentState],
                                                          action: str,
                                                          ) -> None:
    """
    Preserve converted bytes and timestamps through both actual GUI launch paths.
    """
    window, state = imported_window
    image = state.artifact(cst.ARTI_IMG_RAW)
    assert image is not None
    before, modified = image.read_bytes(), image.stat().st_mtime_ns
    root = Path(window.adapter.run_dir)
    backups = set(root.glob('**/.acquisition/backup/**/proc_array_raw.tif'))
    widget = window._editors[cst.StepName.CONVERT].widgets['channel_labels']
    assert isinstance(widget, ConversionChannelsWidget)
    widget.set_labels(['GFP'])
    window.adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', ['GFP'])
    if action == 'next':
        window._next_from_convert()
    else:
        window._show_step(cst.StepName.REGISTER_TIME)
        window._run_pipeline()
    assert window._worker is not None and not window._worker.force_conversion
    deadline = monotonic() + 15
    while window._thread is not None and monotonic() < deadline:
        QTest.qWait(5)
        sleep(0.001)
    assert window._thread is None, window.console.toPlainText()
    assert window._last_run_succeeded, window.console.toPlainText()
    assert image.read_bytes() == before
    assert image.stat().st_mtime_ns == modified
    assert set(root.glob('**/.acquisition/backup/**/proc_array_raw.tif')) == backups
    assert len(discover_saved_states(root)) == 2
    assert not window._needs_conversion()


@pytest.mark.parametrize('mode', ['registration', 'segmentation'])
def test_tuners_display_converted_raw_before_upstream_processing(imported_window: tuple[FischMainWindow, ExperimentState],
                                                               monkeypatch: pytest.MonkeyPatch,
                                                               mode: str,
                                                               ) -> None:
    """
    Display channels and pixels when enabled preprocessing has not produced output.
    """
    window, state = imported_window
    window.adapter.set_step_enabled(cst.StepName.BG_SUB, True)
    window.adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', ['GFP'])
    window.adapter.save_to_run_dir()
    root = Path(window.adapter.run_dir)
    if mode == 'registration':
        tuner = RegistrationTunerWindow(experiments_dir=root, initial_path=state.workdir,
                                         time_settings=RegisterTimeSettings())
        step = cst.StepName.REGISTER_TIME
    else:
        monkeypatch.setattr(SegmentationTunerWindow, '_initialize_selected_model', lambda self: None)
        monkeypatch.setattr(SegmentationTunerWindow, '_run_preview_when_ready', lambda self: None)
        tuner = SegmentationTunerWindow(experiments_dir=root, initial_path=state.workdir,
                                         segment_settings=SegmentSettings.model_validate({'channels': [{'channel': 'GFP'}]}))
        step = cst.StepName.SEGMENT
    try:
        tuner.show()
        get_application().processEvents()
        assert [tuner.channel_combo.itemText(index) for index in range(tuner.channel_combo.count())] == ['GFP']
        assert tuner.image_viewer.image_item.image is not None
        assert tuner._source_path == state.artifact(cst.ARTI_IMG_RAW)
        assert 'Preview uses proc_array_raw.tif' in tuner.status_label.text()
        assert 'background-subtracted image' in tuner.status_label.toolTip()
        tuner.status_label.setText('Preview ready')
        assert 'background-subtracted image' in tuner.status_label.toolTip()
        profile = configured_profile(REGISTRY[step].profile, window.adapter.as_mapping())
        with pytest.raises(ValueError, match='missing image_background_subtracted'):
            resolve_inputs(state, profile)
    finally:
        tuner.close()
        tuner.deleteLater()
        get_application().processEvents()


def test_portable_tuner_guard_preserves_containing_run_checks(imported_window: tuple[FischMainWindow, ExperimentState]) -> None:
    """
    Recognize acquisition-owned state without bypassing a mixed established run.
    """
    window, state = imported_window
    image = state.artifact(cst.ARTI_IMG_RAW)
    assert image is not None
    require_current_source(image)
    window.adapter.save_to_run_dir()
    legacy = Path(window.adapter.run_dir) / 'legacy'
    legacy.mkdir()
    tifffile.imwrite(legacy / cst.ARRAY_RAW, np.ones((8, 8), dtype=np.uint16))
    with pytest.raises(ValueError, match='outdated/read-only'):
        require_current_source(image)


@pytest.mark.parametrize('requested, expected', [(['GFP'], 'GFP'), (['New'], 'New'), ([], 'C1')])
def test_real_conversion_uses_chosen_names_for_all_inputs(tmp_path: Path, requested: list[str], expected: str) -> None:
    """
    Run fresh conversion after relabeling and verify both acquisitions are current.
    """
    root = tmp_path / 'combined'
    old = _processed(root, 'old', ['GFP'])
    tifffile.imwrite(root / 'fresh.tif', np.ones((8, 8), dtype=np.uint16), photometric='minisblack')
    update = prepare_conversion_labels(root, [expected])
    assert update is not None
    apply_labels(update.plan, update.proposed)
    path = old.artifact(cst.ARTI_IMG_RAW)
    assert path is not None
    before = path.read_bytes()
    adapter = SettingsAdapter()
    adapter.run_dir, adapter.user_name = str(root), 'Test'
    adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', requested)
    start_pipeline(adapter.save_to_run_dir(), convert_only=True, terminal_progress=False)
    states = discover_saved_states(root)
    assert len(states) == 2
    for state in states:
        image = state.artifact(cst.ARTI_IMG_RAW)
        assert image is not None and ScopeIO.from_path(image).channel_labels == [expected]
    assert path.read_bytes() == before
    assert not inspect_run(root, adapter.as_mapping(), for_execution=False).conflicts
