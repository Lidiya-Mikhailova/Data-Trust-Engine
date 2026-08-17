from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CBStateStore:
    def __init__(self, persist_path: Optional[str] = None) -> None:
        self._persist_path = persist_path
        self._state: dict[str, dict[str, Any]] = {}
        if persist_path:
            self._load_from_file()

    def get(self, source_id: str) -> dict[str, Any] | None:
        return self._state.get(source_id)

    def put(self, source_id: str, state: dict[str, Any]) -> None:
        self._state[source_id] = state
        if self._persist_path:
            self._save_to_file()
        logger.debug(
            "CB state stored",
            extra={"source_id": source_id, "state": state.get("state")},
        )

    def delete(self, source_id: str) -> None:
        self._state.pop(source_id, None)
        if self._persist_path:
            self._save_to_file()

    def list_sources(self) -> list[str]:
        return list(self._state.keys())

    def clear(self) -> None:
        self._state.clear()
        if self._persist_path:
            self._save_to_file()

    def _save_to_file(self) -> None:
        try:
            dir_path = os.path.dirname(self._persist_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            with open(self._persist_path, "w") as f:
                json.dump(self._state, f, indent=2)
        except OSError as exc:
            logger.warning(
                "Failed to persist CB state",
                extra={"path": self._persist_path, "error": str(exc)},
            )

    def _load_from_file(self) -> None:
        try:
            with open(self._persist_path) as f:
                self._state = json.load(f)
            logger.debug(
                "CB state loaded from file",
                extra={"path": self._persist_path, "sources": list(self._state.keys())},
            )
        except FileNotFoundError:
            self._state = {}
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to load CB state from file",
                extra={"path": self._persist_path, "error": str(exc)},
            )
            self._state = {}
