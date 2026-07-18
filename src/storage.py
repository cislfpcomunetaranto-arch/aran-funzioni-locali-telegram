\
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_STATE = {
    "initialized": False,
    "published_ids": [],
    "last_run_utc": None,
}


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_STATE.copy()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return DEFAULT_STATE.copy()

    state = DEFAULT_STATE.copy()
    state.update(data)
    state["published_ids"] = [str(value) for value in state["published_ids"]]
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["last_run_utc"] = datetime.now(timezone.utc).isoformat()
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
