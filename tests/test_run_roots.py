"""Run selection and adoption of portable acquisitions into new runs."""

from pathlib import Path
import shutil

import numpy as np
import pytest
import tifffile

from fisch.environment import constant as cst
from fisch.gui.settings import SettingsAdapter
from fisch.pipeline import start_pipeline
from fisch.settings.loader import run_settings_path
from fisch.workflows.experiments import discover_saved_states
from fisch.workflows.experiments.discovery import collect_supported_files
from fisch.workflows.experiments.exclusion import set_excluded
from fisch.workflows.experiments.roots import resolve_run_root


@pytest.mark.parametrize('marker', ['.pipeline/settings.toml', '.pipeline/logs', '.fits/fits_settings.toml', '.fits/logs'])
def test_selection_uses_nearest_established_run(tmp_path: Path, marker: str) -> None:
    """
    Resolve fresh, processed, and empty series folders to their containing run.
    """
    target = tmp_path / marker
    target.parent.mkdir(parents=True)
    if target.name == 'logs':
        target.mkdir()
    else:
        target.touch()
    for name in ('fresh', 'portable', 'empty_series'):
        selected = tmp_path / name
        selected.mkdir()
        if name == 'fresh':
            (selected / 'input.nd2').touch()
        elif name == 'portable':
            (selected / '.acquisition').mkdir()
        assert resolve_run_root(selected) == tmp_path
    assert resolve_run_root(tmp_path) == tmp_path
    nested = tmp_path / 'nested'
    (nested / '.pipeline/logs').mkdir(parents=True)
    assert resolve_run_root(nested) == nested
    assert resolve_run_root(nested / 'series') == nested


@pytest.mark.parametrize('excluded', [False, True])
@pytest.mark.parametrize('nested_metadata', [False, True])
def test_new_run_adopts_portable_and_fresh_inputs(tmp_path: Path, excluded: bool, nested_metadata: bool) -> None:
    """
    Process fresh data without overwriting imported results or nested run metadata.
    """
    source = tmp_path / 'source'
    source.mkdir()
    pixels = np.arange(64, dtype=np.uint16).reshape(8, 8)
    tifffile.imwrite(source / 'processed.tif', pixels, photometric='minisblack')
    adapter = SettingsAdapter()
    adapter.run_dir = str(source)
    adapter.user_name = 'Source'
    adapter.set_runtime_value('execution', 'batch')
    adapter.set_field_value(cst.StepName.CONVERT, 'channel_labels', ['Red'])
    start_pipeline(adapter.save_to_run_dir(), terminal_progress=False)
    original = discover_saved_states(source)[0]
    set_excluded(source, [original.workdir], excluded)

    destination = tmp_path / 'combined'
    old_run = destination / 'old_run'
    old_run.mkdir(parents=True)
    shutil.copytree(original.original_image.parent, old_run / 'processed')
    nested_settings = run_settings_path(old_run)
    if nested_metadata:
        shutil.copytree(source / '.pipeline', old_run / '.pipeline')
        # Internal history images must never become fresh conversion inputs.
        tifffile.imwrite(old_run / '.pipeline' / 'history.tif', pixels, photometric='minisblack')
    nested_before = nested_settings.read_bytes() if nested_metadata else None
    fresh = destination / 'fresh.tif'
    tifffile.imwrite(fresh, pixels, photometric='minisblack')
    imported = discover_saved_states(destination)[0]
    converted = imported.artifact(cst.ARTI_IMG_RAW)
    assert converted is not None
    converted_before = converted.read_bytes()
    assert resolve_run_root(destination) == destination
    assert not run_settings_path(destination).exists()
    assert collect_supported_files(destination) == sorted([imported.original_image, fresh])

    # Use an external settings file so CLI resolution is exercised before the
    # destination has either saved settings or logs identifying an established run.
    adapter.run_dir = str(destination)
    adapter.user_name = 'Destination'
    configuration = tmp_path / 'destination.toml'
    shutil.copyfile(adapter.save_to_run_dir(), configuration)
    shutil.rmtree(destination / '.pipeline')
    start_pipeline(configuration, terminal_progress=False)
    states = discover_saved_states(destination)
    assert len(states) == 2
    retained = next(state for state in states if state.workdir == imported.workdir)
    assert retained.excluded is excluded
    assert converted.read_bytes() == converted_before
    assert retained.original_image.is_file()
    assert (nested_settings.read_bytes() if nested_metadata else None) == nested_before
    assert (destination / '.pipeline/logs').is_dir()
    assert resolve_run_root(retained.workdir) == (old_run if nested_metadata else destination)
    fresh_state = next(state for state in states if state.workdir != imported.workdir)
    assert resolve_run_root(fresh_state.workdir) == destination
