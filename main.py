from __future__ import annotations

import logging
import sys

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from app.infrastructure.logging.logger import get_logger, log_both, log_file
from app.ui.bootstrap_worker import BootstrapWorker
from app.ui.loading_screen import LoadingScreen
from app.ui.main_window import MainWindow


logger = get_logger(__name__)


class StartupController(QObject):
    request_open_main = Signal(object)

    def __init__(self, app: QApplication, loading: LoadingScreen) -> None:
        super().__init__()
        self._app = app
        self._loading = loading
        self._runtime = None
        self._window: MainWindow | None = None
        self._bootstrap_thread: QThread | None = None

        self.request_open_main.connect(self._open_main_window)

    def set_bootstrap_thread(self, thread: QThread) -> None:
        self._bootstrap_thread = thread

    @Slot(str, int)
    def on_progress(self, message: str, value: int) -> None:
        self._loading.set_progress(message, value)

    @Slot(object)
    def on_finished(self, runtime: object) -> None:
        log_both(logger, logging.INFO, "Bootstrap terminado correctamente en hilo principal.")

        self._runtime = runtime

        if self._bootstrap_thread is not None:
            self._bootstrap_thread.quit()

        self.request_open_main.emit(runtime)

    @Slot(str)
    def on_failed(self, error_message: str) -> None:
        log_both(logger, logging.ERROR, "Bootstrap falló: %s", error_message)

        self._loading.close()

        QMessageBox.critical(
            None,
            "Error de inicio",
            f"No fue posible inicializar la aplicación.\n\n{error_message}",
        )
        self._app.quit()

    @Slot(object)
    def _open_main_window(self, runtime: object) -> None:
        try:
            log_both(logger, logging.INFO, "Entrando a _open_main_window() en hilo principal.")

            self._app.setApplicationName(runtime.settings.app.name)

            self._window = MainWindow(
                settings=runtime.settings,
                event_bus=runtime.event_bus,
                station_service=runtime.station_service,
            )

            def shutdown_runtime() -> None:
                try:
                    runtime.station_service.stop_station()
                except Exception:
                    log_file(
                        logger,
                        logging.ERROR,
                        "Error al detener station_service al cerrar la app.",
                        exc_info=True,
                    )
                log_both(logger, logging.INFO, "Aplicación finalizada correctamente.")

            self._app.aboutToQuit.connect(shutdown_runtime)

            self._window.show()
            self._loading.close()
            self._app.setQuitOnLastWindowClosed(True)

            log_both(logger, logging.INFO, "MainWindow mostrada correctamente.")

        except Exception as exc:
            log_file(
                logger,
                logging.ERROR,
                "Error abriendo MainWindow.",
                exc_info=True,
            )
            self._loading.close()
            QMessageBox.critical(
                None,
                "Error de inicio",
                f"No fue posible abrir la ventana principal.\n\n{exc}",
            )
            self._app.quit()


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ONT Tester NEXUS")
    app.setQuitOnLastWindowClosed(False)

    loading = LoadingScreen(
        image_path="data/assets/loading_logo.png",
        width=420,
        height=260,
    )
    loading.set_progress("Iniciando...", 0)
    loading.show()
    app.processEvents()

    controller = StartupController(app, loading)

    bootstrap_thread = QThread()
    bootstrap_worker = BootstrapWorker()
    bootstrap_worker.moveToThread(bootstrap_thread)

    controller.set_bootstrap_thread(bootstrap_thread)

    bootstrap_worker.progress_changed.connect(controller.on_progress)
    bootstrap_worker.bootstrap_finished.connect(controller.on_finished)
    bootstrap_worker.bootstrap_failed.connect(controller.on_failed)

    bootstrap_thread.started.connect(bootstrap_worker.run)
    bootstrap_thread.finished.connect(bootstrap_worker.deleteLater)
    bootstrap_thread.finished.connect(bootstrap_thread.deleteLater)

    bootstrap_thread.start()

    return app.exec()


def main() -> int:
    try:
        return run()
    except KeyboardInterrupt:
        log_both(logger, logging.WARNING, "Ejecución interrumpida por el usuario.")
        return 130
    except Exception:
        log_file(
            logger,
            logging.ERROR,
            "Excepción no controlada en el hilo principal.",
            exc_info=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())