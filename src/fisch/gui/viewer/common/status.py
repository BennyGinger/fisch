"""Readable status messages shared by image viewers and tuners."""

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget


class ViewerStatusLabel(QLabel):
    """Keep the complete message available even in a compact viewer footer."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        """
        Allow copying messages and expose their complete text on hover.
        """
        super().__init__(parent)
        self._message = ''
        self._context_warning = ''
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setText(text)

    def setText(self, text: str) -> None:
        """
        Refresh the full, wrapping tooltip whenever the message changes.
        """
        self._message = text
        self._refresh_message()

    def set_context_warning(self, warning: str) -> None:
        """
        Retain an input warning while preview progress messages change.
        """
        self._context_warning = warning
        self._refresh_message()

    def _refresh_message(self) -> None:
        """
        Render the current message with its persistent preview-input warning.
        """
        text = ('⚠ ' + self._context_warning + '\n' + self._message) if self._context_warning else self._message
        super().setText(text)
        self.setToolTip('<qt>' + escape(text).replace('\n', '<br>') + '</qt>')
