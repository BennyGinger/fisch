"""Responsive execution of reviewed file writes for shared GUI dialogs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar
from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout, QWidget

_TaskResult = TypeVar("_TaskResult")


class _FileWorker(QThread):
    def __init__(self, action: Callable[[], Any], parent: QWidget) -> None:
        """
        Initialize the _FileWorker state and dependencies.
        """
        super().__init__(parent)
        self.action = action
        self.error: Exception | None = None
        self.result: Any = None
    def run(self) -> None:
        """
        Execute the background worker operation.
        """
        try:
            self.result = self.action()
        except Exception as error:
            self.error = error



class _Busy(QDialog):
    worker: _FileWorker
    ready_to_close: bool = False
    def reject(self) -> None:
        """
        Reject.
        """
        if self.ready_to_close:
            super().reject()
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Stop active work and handle the window close event.
        """
        if not self.ready_to_close:
            event.ignore()
        else:
            super().closeEvent(event)



def run_file_task(action: Callable[[], _TaskResult],
                  parent: QWidget | None = None,
                  *,
                  title: str = 'Updating experiment files',
                  message: str = 'Updating files and verifying the result…',
                  apply_result: Callable[[_TaskResult], None] | None = None,
                  ) -> _TaskResult:
    """
    Run reviewed file operations in a worker while keeping progress responsive.
    """
    dialog = _Busy(parent)
    dialog.setWindowTitle(title)
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel(message))
    progress = QProgressBar()
    progress.setRange(0, 0)
    layout.addWidget(progress)
    worker = _FileWorker(action, dialog)
    dialog.worker = worker
    def finish() -> None:
        """
        Keep progress visible while the GUI applies the inspected results.
        """
        if worker.error is None and apply_result is not None:
            try:
                apply_result(worker.result)
            except Exception as error:
                worker.error = error
        dialog.ready_to_close = True
        QTimer.singleShot(0, dialog.accept)

    worker.finished.connect(finish, Qt.ConnectionType.QueuedConnection)
    worker.start()
    dialog.exec()
    worker.wait()
    if worker.error is not None:
        raise worker.error
    return worker.result

