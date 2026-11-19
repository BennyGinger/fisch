"""File management inspects in the background before showing available actions."""

from pathlib import Path
from threading import Event, get_ident
from typing import Any

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QProgressBar

import fisch.gui.file_management.manager as manager
from fisch.gui.theme import get_application
from fisch.gui.main_window.window import FischMainWindow
from fisch.gui.settings import SettingsAdapter
from fisch.environment.constant import StepName
from fisch.workflows.checks.models import RunCompatibility


def test_manage_files_processing_screen_and_reused_compatibility(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Reuse a checked root and keep the UI responsive through manager inspection.
    """
    app = get_application()
    status = RunCompatibility(tmp_path, (), (), (), ())
    release = Event()
    observed: dict[str, Any] = {}
    original = manager._inspect_management
    main_thread = get_ident()

    def inspect(root: Path,
                selected: Path | None,
                compatibility: RunCompatibility | None,
                input_problem: str,
                input_warning: str,
                ) -> Any:
        """
        Wait until the GUI timer observes the Processing dialog.
        """
        observed['worker'] = get_ident() != main_thread
        observed['reused_status'] = compatibility is status
        if not release.wait(timeout=5):
            raise RuntimeError('The GUI did not remain responsive during inspection')
        return original(root, selected, compatibility, input_problem, input_warning)

    def observe() -> None:
        """
        Confirm visible progress and allow the background inspection to finish.
        """
        try:
            dialog = app.activeModalWidget()
            observed['processing'] = isinstance(dialog, QDialog) and dialog.windowTitle() == 'Processing'
            bar = dialog.findChild(QProgressBar) if dialog is not None else None
            observed['busy'] = bar is not None and bar.minimum() == bar.maximum() == 0
        finally:
            release.set()
        QTimer.singleShot(10, close_manager)

    def close_manager() -> None:
        """
        Close after inspection and the label pane's own background read finish.
        """
        dialog = app.activeModalWidget()
        if isinstance(dialog, QDialog) and dialog.windowTitle() == 'Manage experiment files':
            editor = getattr(dialog, 'channel_editor', None)
            if editor is None or not editor.is_busy:
                observed['manager'] = True
                dialog.reject()
                return
        QTimer.singleShot(10, close_manager)

    def unexpected_check(root: Path) -> RunCompatibility:
        """
        Fail if the manager repeats the already supplied compatibility scan.
        """
        raise AssertionError('Repeated compatibility inspection')

    monkeypatch.setattr(manager, '_inspect_management', inspect)
    monkeypatch.setattr(manager, 'inspect_run_compatibility', unexpected_check)
    QTimer.singleShot(30, observe)
    assert not manager.manage_files(tmp_path, compatibility=status)
    assert observed == {'worker': True, 'reused_status': True, 'processing': True, 'busy': True, 'manager': True}


@pytest.mark.usefixtures('inline_inspection_dialogs')
@pytest.mark.parametrize('changed', [False, True])
def test_manager_only_refreshes_after_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: bool) -> None:
    """
    Leave the existing view intact on Close and refresh once after a file action.
    """
    app = get_application()
    adapter = SettingsAdapter()
    adapter.run_dir = str(tmp_path)
    window = FischMainWindow(adapter)
    refreshed: list[tuple[StepName, Path | None]] = []
    previous_step = window._current_step
    selected = window.run_browser.selected_path

    def close_manager(*args: Any, **kwargs: Any) -> bool:
        """
        Return the manager's established change result without touching files.
        """
        return changed

    def refresh(step: StepName, selection: Path | None) -> None:
        """
        Observe refresh requests without running another inspection.
        """
        refreshed.append((step, selection))

    monkeypatch.setattr('fisch.gui.main_window.window.manage_files', close_manager)
    monkeypatch.setattr(window, '_refresh_after_file_management', refresh)
    try:
        window._manage_files()
        assert refreshed == ([(previous_step, selected)] if changed else [])
        assert window._current_step == previous_step
        assert window.run_browser.selected_path == selected
        assert not list(tmp_path.iterdir())
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()
