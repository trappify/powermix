from __future__ import annotations

from typing import Any


class DummyState:
    def __init__(self, state: Any, attributes: dict[str, Any] | None = None) -> None:
        self.state = state
        self.attributes = attributes or {}


class DummyStates:
    def __init__(self) -> None:
        self._data: dict[str, DummyState] = {}

    def set(self, entity_id: str, state: Any, attributes: dict[str, Any] | None = None) -> None:
        self._data[entity_id] = DummyState(state, attributes)

    def remove(self, entity_id: str) -> None:
        self._data.pop(entity_id, None)

    def get(self, entity_id: str) -> DummyState | None:
        return self._data.get(entity_id)


class DummyHass:
    def __init__(self) -> None:
        self.states = DummyStates()
        self.data: dict[str, Any] = {}
