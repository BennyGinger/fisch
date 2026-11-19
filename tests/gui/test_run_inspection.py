"""Initial inspection gives feedback while metadata is read off the GUI thread."""

from collections.abc import Mapping
from pathlib import Path
from threading import Event, get_ident
from typing import Any

import numpy as np
import pytest
import tifffile
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QProgressBar

from fisch.environment.constant import StepName
from fisch.gui.main_window.window import FischMainWindow
from fisch.gui.main_window.inspection import RunInspection
from fisch.gui.settings import SettingsAdapter
from fisch.gui.theme import get_application


@pytest.mark.parametrize('saved_settings', [False, True])
def test_open_inspects_once_with_responsive_processing_dialog(tmp_path: Path,
                                                             monkeypatch: pytest.MonkeyPatch,
                                                             saved_settings: bool,
                                                             ) -> None:
    """
    Show the modal progress indicator and load saved settings before inspecting.
    """
    app = get_application()
    tifffile.imwrite(tmp_path / 'input.tif', np.ones((8, 8), dtype=np.uint16), photometric='minisblack')
    if saved_settings:
        saved = SettingsAdapter()
        saved.run_dir, saved.user_name = str(tmp_path), 'Saved user'
        saved.set_field_value(StepName.CONVERT, 'channel_labels', ['GFP'])
        saved.save_to_run_dir()
    window = FischMainWindow(SettingsAdapter())
    original = window._inspect_run_inventory
    release = Event()
    inspected: list[tuple[int, list[str]]] = []
    observed: dict[str, Any] = {}
    main_thread = get_ident()
    original_apply = window._apply_run_inventory

    def inspect(root: Path | None,
                config: Mapping[str, Any],
                ) -> RunInspection:
        """
        Hold inspection until a GUI timer has observed the Processing dialog.
        """
        inspected.append((get_ident(), list(config['convert']['params']['channel_labels'])))
        if not release.wait(timeout=5):
            raise RuntimeError('GUI did not process its timer during inspection')
        return original(root, config)

    def observe() -> None:
        """
        Record visible progress and release the worker from the GUI event loop.
        """
        try:
            dialog = app.activeModalWidget()
            observed['dialog'] = isinstance(dialog, QDialog)
            if isinstance(dialog, QDialog):
                observed['title'] = dialog.windowTitle()
                bar = dialog.findChild(QProgressBar)
                observed['busy'] = bar is not None and bar.minimum() == bar.maximum() == 0
        finally:
            release.set()

    def apply_result(inspection: RunInspection) -> None:
        """
        Verify the wait screen remains visible through the GUI update.
        """
        dialog = app.activeModalWidget()
        observed['applying_with_progress'] = isinstance(dialog, QDialog) and dialog.windowTitle() == 'Processing'
        observed['apply_on_main_thread'] = get_ident() == main_thread
        original_apply(inspection)

    monkeypatch.setattr(window, '_inspect_run_inventory', inspect)
    monkeypatch.setattr(window, '_apply_run_inventory', apply_result)
    QTimer.singleShot(30, observe)
    try:
        window._switch_run_dir(str(tmp_path))
        assert observed == {'dialog': True, 'title': 'Processing', 'busy': True,
                            'applying_with_progress': True, 'apply_on_main_thread': True}
        assert len(inspected) == 1
        assert inspected[0][0] != main_thread
        assert inspected[0][1] == (['GFP'] if saved_settings else [])
        assert Path(window.adapter.run_dir) == tmp_path
        assert window._raw_input_report is not None
        assert set(window._raw_input_report.channel_counts.values()) == {1}
    finally:
        release.set()
        window.close()
        window.deleteLater()
        app.processEvents()
