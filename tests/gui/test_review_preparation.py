"""Check launch preparation without starting processing or loading a model."""

from pathlib import Path
from typing import cast

import numpy as np
import tifffile
from PySide6.QtWidgets import QApplication, QWidget

from fisch.gui.main_window.window import FischMainWindow
from fisch.gui.settings import SettingsAdapter
from fisch.workflows.checks.models import RawInputReport
from fisch.environment.constant import StepName


class _LaunchHarness(QWidget):
    """Exercise preflight preparation and stop before a worker could be created."""

    def __init__(self, root: Path) -> None:
        """
        Store draft settings and observe only the source inspection/save boundary.
        """
        super().__init__()
        self.adapter = SettingsAdapter()
        self.adapter.run_dir = str(root)
        self._run_status = None
        self.raw: RawInputReport | None = None
        self.save_refresh: list[bool] = []

    def _apply_raw_input_report(self, report: RawInputReport | None) -> None:
        """
        Receive inspected metadata without constructing the full settings GUI.
        """
        self.raw = report

    def _raw_input_error(self) -> str:
        """
        Reuse the source check's error details.
        """
        return self.raw.describe() if self.raw is not None else ''

    def _enabled_step_input_problems(self) -> dict[StepName, str]:
        """
        Keep this check focused on conversion source inspection.
        """
        return {}

    def _sync_identity(self) -> None:
        """
        Leave this fixed test draft unchanged.
        """

    def _save_settings(self, *, refresh_inventory: bool = True) -> Path | None:
        """
        Record the requested refresh policy and prevent any pipeline launch.
        """
        self.save_refresh.append(refresh_inventory)
        return None


def test_launch_checks_sources_without_duplicate_gui_preflight(tmp_path: Path) -> None:
    """
    Refresh input dimensions but leave authoritative artifact preflight to the worker.
    """
    app = QApplication.instance() or QApplication([])
    source = tmp_path / 'input.tif'
    tifffile.imwrite(source, np.ones((8, 8), dtype=np.uint16), photometric='minisblack')
    window = _LaunchHarness(tmp_path)
    try:
        FischMainWindow._launch_pipeline(cast(FischMainWindow, window), convert_only=False)
        assert window.save_refresh == [False]
        assert window.raw is not None and window.raw.channel_counts == {source: 1}
        assert not (tmp_path / '.pipeline').exists()
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()
