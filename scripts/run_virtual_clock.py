"""Helper script for launching the virtual clock from the command line."""
from __future__ import annotations

import time

from app_library.loader import launch_app


def main() -> None:
    app = launch_app("virtual_clock")
    try:
        while app.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()


if __name__ == "__main__":
    main()
