import json
import os
from pathlib import Path
from unittest.mock import Mock

from src.presets import MAX_PRESET_SIZE, PresetStore, cleanup_choice_key


def test_cleanup_choice_key_contains_name_and_normalized_path(tmp_path):
    key = cleanup_choice_key("Cache", str(tmp_path / "folder" / ".." / "cache"))

    assert key.startswith("cleanup:Cache:")
    assert key.endswith(os.path.normcase(str(tmp_path / "cache")))


def test_preset_store_round_trip_uses_versioned_json(tmp_path):
    path = tmp_path / "PC_CLEANER" / "preset.json"
    store = PresetStore(path)
    choices = {"cleanup:Cache:C:\\Cache": True, "action:flush-dns": False}

    assert store.save(choices) is True
    assert store.load() == choices
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1
    assert not list(path.parent.glob("*.tmp"))


def test_preset_store_rejects_invalid_choices(tmp_path):
    store = PresetStore(tmp_path / "preset.json")

    assert store.save({"not-a-bool": "yes"}) is False
    assert not store.path.exists()


def test_preset_store_ignores_missing_malformed_or_incompatible_files(tmp_path):
    path = tmp_path / "preset.json"
    store = PresetStore(path)
    assert store.load() is None

    path.write_text("not json", encoding="utf-8")
    assert store.load() is None

    path.write_text(json.dumps({"version": 99, "choices": {}}), encoding="utf-8")
    assert store.load() is None

    path.write_text(
        json.dumps({"version": 1, "choices": {"cache": "yes"}}),
        encoding="utf-8",
    )
    assert store.load() is None


def test_preset_store_ignores_oversized_file(tmp_path):
    path = tmp_path / "preset.json"
    path.write_bytes(b"x" * (MAX_PRESET_SIZE + 1))

    assert PresetStore(path).load() is None


def test_preset_store_returns_false_when_parent_cannot_be_created(
    tmp_path, monkeypatch
):
    store = PresetStore(tmp_path / "preset.json")

    def deny_creation(*_args, **_kwargs):
        raise OSError("denied")

    monkeypatch.setattr(Path, "mkdir", deny_creation)

    assert store.save({"cache": True}) is False


def test_preset_store_cleans_temporary_file_after_replace_failure(
    tmp_path, monkeypatch
):
    store = PresetStore(tmp_path / "preset.json")
    unlink_mock = Mock()
    monkeypatch.setattr("src.presets.os.replace", Mock(side_effect=OSError("denied")))
    monkeypatch.setattr(Path, "unlink", unlink_mock)

    assert store.save({"cache": True}) is False
    unlink_mock.assert_called_once_with(missing_ok=True)
