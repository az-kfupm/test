"""Stub hardware interface for mapping button events to navigation actions."""

from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, List


class NavigationAction(str, Enum):
    """High-level navigation actions driven by hardware buttons."""

    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    SELECT = "select"
    BACK = "back"


class HardwareInterface:
    """Simplified hardware abstraction for button-driven navigation."""

    def __init__(self) -> None:
        self._button_bindings: Dict[str, NavigationAction] = {}
        self._action_listeners: List[Callable[[NavigationAction], None]] = []

    def bind_button(self, button_id: str, action: NavigationAction) -> None:
        """Associate a hardware *button_id* with a navigation *action*."""

        self._button_bindings[button_id] = action

    def register_listener(self, listener: Callable[[NavigationAction], None]) -> None:
        """Register a callback invoked when a navigation *action* occurs."""

        self._action_listeners.append(listener)

    def emit_button_event(self, button_id: str) -> None:
        """Convert a raw button event into a navigation action and dispatch it."""

        action = self._button_bindings.get(button_id)
        if action is None:
            return
        for listener in list(self._action_listeners):
            listener(action)

    def default_bindings(self) -> None:
        """Configure default button bindings for a standard controller."""

        self.bind_button("up", NavigationAction.MOVE_UP)
        self.bind_button("down", NavigationAction.MOVE_DOWN)
        self.bind_button("enter", NavigationAction.SELECT)
        self.bind_button("back", NavigationAction.BACK)
