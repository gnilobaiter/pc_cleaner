from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

from src.config import get_appdata_dir

PRESET_SCHEMA_VERSION = 1
MAX_PRESET_SIZE = 1024 * 1024


def cleanup_choice_key(name: str, path: str) -> str:
    return f"cleanup:{name}:{os.path.normcase(os.path.abspath(path))}"


class PresetStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or get_appdata_dir() / "PC_CLEANER" / "preset.json"

    def load(self) -> Optional[Dict[str, bool]]:
        try:
            if not self.path.is_file() or self.path.stat().st_size > MAX_PRESET_SIZE:
                return None
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None

        if (
            not isinstance(payload, dict)
            or payload.get("version") != PRESET_SCHEMA_VERSION
        ):
            return None
        choices = payload.get("choices")
        if not isinstance(choices, dict) or not all(
            isinstance(key, str) and isinstance(value, bool)
            for key, value in choices.items()
        ):
            return None
        return choices

    def save(self, choices: Dict[str, bool]) -> bool:
        if not all(
            isinstance(key, str) and isinstance(value, bool)
            for key, value in choices.items()
        ):
            return False

        temporary_path: Optional[Path] = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"version": PRESET_SCHEMA_VERSION, "choices": choices}
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=str(self.path.parent),
                prefix="preset-",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                json.dump(payload, temporary_file, indent=2, sort_keys=True)
                temporary_file.write("\n")
                temporary_path = Path(temporary_file.name)
            os.replace(str(temporary_path), str(self.path))
            return True
        except (OSError, TypeError, ValueError):
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            return False
