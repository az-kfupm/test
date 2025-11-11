"""Command-line entry point for Table OS."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from table_os.app_registry import AppRegistry
from table_os.hardware_interface import HardwareInterface, NavigationAction


def render_menu(app_names: List[str], descriptions: List[str], selected_index: int) -> None:
    """Render the application menu to stdout."""

    print("\n=== Table OS ===")
    if not app_names:
        print("No applications available. Add manifest files to get started.")
        return

    for index, name in enumerate(app_names):
        prefix = "->" if index == selected_index else "  "
        description = descriptions[index]
        if description:
            print(f"{prefix} {name} - {description}")
        else:
            print(f"{prefix} {name}")
    print("\nType one of: up, down, enter, back, quit")


def boot(manifest_locations: List[str]) -> int:
    """Boot Table OS with manifests discovered from *manifest_locations*."""

    registry = AppRegistry()
    if manifest_locations:
        registry.discover(manifest_locations)

    apps = registry.list_apps()
    if not apps:
        render_menu([], [], 0)
        return 1

    app_names = [metadata.name for metadata in apps]
    descriptions = [metadata.description or "" for metadata in apps]
    selected_index = 0
    active_app_name: Optional[str] = None

    hardware = HardwareInterface()
    hardware.default_bindings()

    def handle_navigation(action: NavigationAction) -> None:
        nonlocal selected_index, active_app_name

        if action == NavigationAction.MOVE_UP:
            selected_index = (selected_index - 1) % len(app_names)
        elif action == NavigationAction.MOVE_DOWN:
            selected_index = (selected_index + 1) % len(app_names)
        elif action == NavigationAction.SELECT:
            target_name = app_names[selected_index]
            if active_app_name and active_app_name != target_name:
                registry.stop(active_app_name)
            if not registry.is_running(target_name):
                registry.launch(target_name)
                print(f"\nLaunched {target_name}\n")
            active_app_name = target_name
        elif action == NavigationAction.BACK:
            if active_app_name:
                registry.stop(active_app_name)
                print(f"\nStopped {active_app_name}\n")
                active_app_name = None

    hardware.register_listener(handle_navigation)

    try:
        while True:
            render_menu(app_names, descriptions, selected_index)
            command = input("> ").strip().lower()
            if command in {"quit", "exit"}:
                break
            if command == "":
                continue
            hardware.emit_button_event(command)
    except KeyboardInterrupt:
        print("\nExiting Table OS.")
    finally:
        registry.stop_all()
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Table OS shell")
    parser.add_argument(
        "--manifests",
        "-m",
        action="append",
        default=[],
        help="Paths to manifest files or directories containing manifests.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    manifest_locations = args.manifests or [str(Path("manifests"))]
    return boot(manifest_locations)


if __name__ == "__main__":
    raise SystemExit(main())
