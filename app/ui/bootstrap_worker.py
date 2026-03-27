from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.startup.bootstrap_runtime import RuntimeBundle, bootstrap_runtime


class BootstrapWorker(QObject):
    progress_changed = Signal(str, int)
    bootstrap_finished = Signal(object)
    bootstrap_failed = Signal(str)

    @Slot()
    def run(self) -> None:
        try:
            runtime = bootstrap_runtime(self._emit_progress)
            self.bootstrap_finished.emit(runtime)
        except Exception as exc:
            self.bootstrap_failed.emit(str(exc))

    def _emit_progress(self, message: str, value: int) -> None:
        self.progress_changed.emit(message, value)