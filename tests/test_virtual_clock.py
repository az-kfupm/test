from __future__ import annotations

import json
import sys
import time
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_library.loader import get_app_entry, launch_app, list_apps
from apps.virtual_clock.app import VirtualClockApp


def test_global_manifest_registers_virtual_clock() -> None:
    manifest_path = Path("apps/manifest.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next((app for app in data["apps"] if app["id"] == "virtual_clock"), None)
    assert entry is not None
    assert entry["entry_point"] == "apps.virtual_clock.app:VirtualClockApp"
    assert entry["manifest"] == "apps/virtual_clock/manifest.json"


def test_launch_app_returns_virtual_clock_instance(monkeypatch) -> None:
    started = {}

    def fake_start(self):
        started["called"] = True

    monkeypatch.setattr(VirtualClockApp, "start", fake_start)
    app = launch_app("virtual_clock", start=False)
    assert isinstance(app, VirtualClockApp)
    assert "called" not in started


def test_list_apps_accepts_manifest_path() -> None:
    manifest_path = Path("apps/manifest.json")
    apps = list(list_apps(manifest_path))
    assert any(app["id"] == "virtual_clock" for app in apps)


def test_get_app_entry_accepts_manifest_path_string() -> None:
    entry = get_app_entry("virtual_clock", "apps/manifest.json")
    assert entry["entry_point"] == "apps.virtual_clock.app:VirtualClockApp"


class _FakeRoot:
    def __init__(self) -> None:
        self._callbacks = []
        self._quit_event = threading.Event()
        self._destroyed = False
        self.protocols = {}

    def title(self, _text: str) -> None:
        pass

    def after(self, _delay: int, callback):
        self._callbacks.append(callback)
        return len(self._callbacks) - 1

    def after_cancel(self, job_id: int) -> None:
        if 0 <= job_id < len(self._callbacks):
            self._callbacks[job_id] = None

    def protocol(self, name: str, func) -> None:
        self.protocols[name] = func

    def mainloop(self) -> None:
        while not self._quit_event.is_set():
            callbacks = list(self._callbacks)
            self._callbacks = []
            for callback in callbacks:
                if callback is None:
                    continue
                callback()
            time.sleep(0.01)

    def quit(self) -> None:
        self._quit_event.set()

    def destroy(self) -> None:
        self._destroyed = True


class _FakeLabel:
    def __init__(self, _root, *, text: str, font):
        self.text_values = [text]
        self.font = font

    def config(self, *, text: str) -> None:
        self.text_values.append(text)

    def pack(self, **_kwargs) -> None:
        pass


class _FakeTkModule:
    def __init__(self) -> None:
        self.created_roots = []
        self.Label = _FakeLabel

    def Tk(self):
        root = _FakeRoot()
        self.created_roots.append(root)
        return root


def test_virtual_clock_start_and_stop_with_fake_tk() -> None:
    fake_tk = _FakeTkModule()
    app = VirtualClockApp(tk_module=fake_tk)
    app.start()

    time.sleep(0.05)
    assert app.running

    app.stop()
    assert not app.running
    assert fake_tk.created_roots[0]._destroyed is True
