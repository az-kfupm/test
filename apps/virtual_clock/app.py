"""Tkinter-based virtual clock application."""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Callable, Optional

import tkinter as tk

from app_library import App


class VirtualClockApp(App):
    """Simple application that renders the current time in a Tkinter window."""

    def __init__(
        self,
        tk_module: Optional[object] = None,
        thread_factory: Optional[Callable[[Callable[[], None]], threading.Thread]] = None,
    ) -> None:
        super().__init__()
        self._tk = tk_module or tk
        self._thread_factory = thread_factory or self._default_thread_factory
        self._ui_thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None
        self._root = None
        self._label = None
        self._update_job = None

    @staticmethod
    def _default_thread_factory(target: Callable[[], None]) -> threading.Thread:
        return threading.Thread(target=target, daemon=True)

    def start(self) -> None:
        if self.running:
            return

        self._stop_event = threading.Event()

        def run_ui() -> None:
            try:
                self._run_ui_loop()
            finally:
                self._finalize_from_ui_thread()

        thread = self._thread_factory(run_ui)
        self._ui_thread = thread
        self._mark_running()

        try:
            starter = getattr(thread, "start", None)
            if callable(starter):
                starter()
        except Exception:
            # Roll back running state if the UI thread fails to start.
            self._mark_stopped()
            self._ui_thread = None
            self._stop_event = None
            raise

    def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()

        thread = self._ui_thread
        if thread is not None and hasattr(thread, "join"):
            thread.join(timeout=5.0)

        self._ui_thread = None
        self._stop_event = None
        self._mark_stopped()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _run_ui_loop(self) -> None:
        root = self._tk.Tk()
        self._root = root
        root.title("Virtual Clock")

        label = self._tk.Label(root, text=self._formatted_time(), font=("Helvetica", 36))
        label.pack(padx=24, pady=24)
        self._label = label

        def update_time() -> None:
            if self._stop_event and self._stop_event.is_set():
                return
            label.config(text=self._formatted_time())
            self._update_job = root.after(1000, update_time)

        def poll_stop() -> None:
            if self._stop_event and self._stop_event.is_set():
                root.quit()
            else:
                root.after(100, poll_stop)

        root.protocol("WM_DELETE_WINDOW", self._handle_close_request)
        update_time()
        root.after(100, poll_stop)

        try:
            root.mainloop()
        finally:
            if self._update_job is not None:
                try:
                    root.after_cancel(self._update_job)
                except Exception:
                    pass
                self._update_job = None

    def _handle_close_request(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()

    def _finalize_from_ui_thread(self) -> None:
        if self._root is not None:
            try:
                self._root.destroy()
            except Exception:
                pass
        self._root = None
        self._label = None
        self._update_job = None
        self._ui_thread = None
        self._stop_event = None
        self._mark_stopped()

    @staticmethod
    def _formatted_time() -> str:
        return datetime.now().strftime("%H:%M:%S")
