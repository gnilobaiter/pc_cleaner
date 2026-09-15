import subprocess
from pathlib import Path
from unittest.mock import Mock

from src.cleaner import Cleaner


def test_clear_folder_deletes_contents_and_returns_size(tmp_path, monkeypatch):
    root = tmp_path / "cache"
    root.mkdir()
    (root / "file.bin").write_bytes(b"abc")
    nested = root / "nested"
    nested.mkdir()
    (nested / "item.bin").write_bytes(b"12345")
    monkeypatch.setattr("src.cleaner.has_access", lambda _: True)

    deleted = Cleaner().clear_folder(root, "Cache")

    assert deleted == 8
    assert list(root.iterdir()) == []


def test_clear_folder_dry_run_preserves_contents(tmp_path, monkeypatch):
    file_path = tmp_path / "file.bin"
    file_path.write_bytes(b"abc")
    monkeypatch.setattr("src.cleaner.has_access", lambda _: True)

    deleted = Cleaner(dry_run=True).clear_folder(tmp_path, "Cache")

    assert deleted == 3
    assert file_path.exists()


def test_clear_folder_skips_inaccessible_or_missing_folder(tmp_path, monkeypatch):
    cleaner = Cleaner()
    monkeypatch.setattr("src.cleaner.has_access", lambda _: False)
    assert cleaner.clear_folder(tmp_path, "Cache") == 0

    monkeypatch.setattr("src.cleaner.has_access", lambda _: True)
    assert cleaner.clear_folder(tmp_path / "missing", "Cache") == 0


def test_get_directory_size_ignores_os_errors(tmp_path, monkeypatch):
    target = tmp_path / "file.bin"
    target.write_bytes(b"abc")
    original_stat = Path.stat

    def failing_stat(path, *args, **kwargs):
        if path == target:
            raise OSError("locked")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", failing_stat)
    assert Cleaner.get_directory_size(tmp_path) == 0


def test_flush_dns_skips_when_not_confirmed(monkeypatch):
    cleaner = Cleaner()
    status_mock = Mock()
    monkeypatch.setattr("src.cleaner.get_user_confirmation", lambda *_: False)
    monkeypatch.setattr(cleaner, "print_status", status_mock)
    run_mock = Mock()
    monkeypatch.setattr("src.cleaner.subprocess.run", run_mock)

    cleaner.flush_dns()

    run_mock.assert_not_called()
    assert "Skipping DNS Flush" in status_mock.call_args.args[0]


def test_flush_dns_reports_success_and_failure(monkeypatch):
    cleaner = Cleaner()
    status_mock = Mock()
    monkeypatch.setattr("src.cleaner.get_user_confirmation", lambda *_: True)
    monkeypatch.setattr(cleaner, "print_status", status_mock)
    run_mock = Mock()
    monkeypatch.setattr("src.cleaner.subprocess.run", run_mock)

    cleaner.flush_dns()
    run_mock.assert_called_once_with(["ipconfig", "/flushdns"], check=True)
    assert any("successfully" in call.args[0] for call in status_mock.call_args_list)

    monkeypatch.setattr("src.cleaner.subprocess.run", Mock(side_effect=subprocess.CalledProcessError(1, "ipconfig")))
    cleaner.flush_dns()
    assert any("Failed to flush" in call.args[0] for call in status_mock.call_args_list)


def test_run_skips_declined_entries_and_prints_total(monkeypatch):
    cleaner = Cleaner()
    status_mock = Mock()
    monkeypatch.setattr("src.cleaner.get_temp_dirs", lambda: [("Safe", "safe", "", False), ("Ask", "ask", "", True)])
    monkeypatch.setattr("src.cleaner.get_user_confirmation", lambda *_: False)
    monkeypatch.setattr(cleaner, "clear_folder", lambda *_: 2048)
    monkeypatch.setattr(cleaner, "flush_dns", Mock())
    monkeypatch.setattr(cleaner, "print_status", status_mock)
    monkeypatch.setattr("builtins.input", lambda _: "")

    cleaner.run()

    assert cleaner.total_deleted_size == 2048
    assert any("Skipping Ask" in call.args[0] for call in status_mock.call_args_list)
    assert any("Total space freed: 2.00 KB" in call.args[0] for call in status_mock.call_args_list)
