import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from src.cleaner import (
    DNS_CHOICE_KEY,
    IO_REPARSE_TAG_AF_UNIX,
    SHERB_NOCONFIRMATION,
    SHERB_NOPROGRESSUI,
    SHERB_NOSOUND,
    Cleaner,
)
from src.presets import cleanup_choice_key


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

    monkeypatch.setattr(
        "src.cleaner.subprocess.run",
        Mock(side_effect=subprocess.CalledProcessError(1, "ipconfig")),
    )
    cleaner.flush_dns()
    assert any("Failed to flush" in call.args[0] for call in status_mock.call_args_list)


def test_run_skips_declined_entries_and_prints_total(monkeypatch):
    preset_store = Mock(load=Mock(return_value=None), save=Mock(return_value=True))
    cleaner = Cleaner(preset_store=preset_store)
    status_mock = Mock()
    monkeypatch.setattr(
        "src.cleaner.get_temp_dirs",
        lambda: [("Safe", "safe", "", False), ("Ask", "ask", "", True)],
    )
    monkeypatch.setattr("src.cleaner.get_user_confirmation", lambda *_: False)
    monkeypatch.setattr(cleaner, "clear_folder", lambda *_: 2048)
    monkeypatch.setattr(cleaner, "flush_dns", Mock())
    monkeypatch.setattr(cleaner, "print_status", status_mock)
    monkeypatch.setattr("builtins.input", lambda _: "")

    cleaner.run()

    assert cleaner.total_deleted_size == 2048
    assert any("Skipping Ask" in call.args[0] for call in status_mock.call_args_list)
    assert any(
        "Total data removed: 2.00 KB" in call.args[0]
        for call in status_mock.call_args_list
    )
    preset_store.save.assert_called_once_with(
        {cleanup_choice_key("Ask", "ask"): False, DNS_CHOICE_KEY: False}
    )


def test_safe_af_unix_reparse_point_is_unlinked_without_following_target():
    path = Mock()
    path.lstat.return_value = SimpleNamespace(
        st_reparse_tag=IO_REPARSE_TAG_AF_UNIX,
        st_mode=0,
        st_size=17,
    )

    assert Cleaner()._remove_safe_reparse_point(path) == 17
    path.unlink.assert_called_once_with()


def test_directory_junction_is_quietly_left_in_place():
    path = Mock()
    path.lstat.return_value = SimpleNamespace(
        st_reparse_tag=0xA0000003,
        st_mode=0,
        st_size=0,
    )
    path.is_symlink.return_value = False

    assert Cleaner()._remove_safe_reparse_point(path) is None
    path.unlink.assert_not_called()


def test_safe_reparse_point_is_preserved_during_dry_run():
    path = Mock()
    path.lstat.return_value = SimpleNamespace(
        st_reparse_tag=IO_REPARSE_TAG_AF_UNIX,
        st_mode=0,
        st_size=5,
    )

    assert Cleaner(dry_run=True)._remove_safe_reparse_point(path) == 5
    path.unlink.assert_not_called()


def test_clear_folder_does_not_log_unsupported_reparse_points(monkeypatch):
    folder = Mock()
    item = Mock()
    folder.exists.return_value = True
    folder.iterdir.return_value = [item]
    cleaner = Cleaner()
    status_mock = Mock()
    monkeypatch.setattr("src.cleaner.is_trusted_cleanup_path", lambda *_: True)
    monkeypatch.setattr("src.cleaner.has_access", lambda *_: True)
    monkeypatch.setattr(cleaner, "_is_reparse_point", lambda path: path is item)
    monkeypatch.setattr(cleaner, "_remove_safe_reparse_point", lambda *_: None)
    monkeypatch.setattr(cleaner, "print_status", status_mock)

    assert cleaner.clear_folder(folder, "Cache") == 0
    status_mock.assert_not_called()


def test_clear_folder_counts_removed_safe_reparse_point(monkeypatch):
    folder = Mock()
    item = Mock()
    folder.exists.return_value = True
    folder.iterdir.return_value = [item]
    cleaner = Cleaner()
    monkeypatch.setattr("src.cleaner.is_trusted_cleanup_path", lambda *_: True)
    monkeypatch.setattr("src.cleaner.has_access", lambda *_: True)
    monkeypatch.setattr(cleaner, "_is_reparse_point", lambda path: path is item)
    monkeypatch.setattr(cleaner, "_remove_safe_reparse_point", lambda *_: 23)

    assert cleaner.clear_folder(folder, "Cache") == 23


def test_clear_folder_ignores_permission_errors_and_reports_other_errors(monkeypatch):
    folder = Mock()
    denied_item = Mock()
    broken_item = Mock()
    folder.exists.return_value = True
    folder.iterdir.return_value = [denied_item, broken_item]
    cleaner = Cleaner()
    status_mock = Mock()
    monkeypatch.setattr("src.cleaner.is_trusted_cleanup_path", lambda *_: True)
    monkeypatch.setattr("src.cleaner.has_access", lambda *_: True)
    monkeypatch.setattr(cleaner, "_is_reparse_point", lambda *_: False)
    denied_item.is_file.side_effect = PermissionError("denied")
    broken_item.is_file.side_effect = RuntimeError("broken")
    monkeypatch.setattr(cleaner, "print_status", status_mock)

    assert cleaner.clear_folder(folder, "Cache") == 0
    assert any(
        "Error processing" in call.args[0] for call in status_mock.call_args_list
    )


def test_clear_folder_reports_directory_listing_failure(monkeypatch):
    folder = Mock()
    folder.exists.return_value = True
    folder.iterdir.side_effect = OSError("broken")
    cleaner = Cleaner()
    status_mock = Mock()
    monkeypatch.setattr("src.cleaner.is_trusted_cleanup_path", lambda *_: True)
    monkeypatch.setattr("src.cleaner.has_access", lambda *_: True)
    monkeypatch.setattr(cleaner, "_is_reparse_point", lambda *_: False)
    monkeypatch.setattr(cleaner, "print_status", status_mock)

    assert cleaner.clear_folder(folder, "Cache") == 0
    assert "Failed to process" in status_mock.call_args.args[0]


def test_clear_folder_rechecks_directory_before_recursive_delete(monkeypatch):
    folder = Mock()
    item = Mock()
    folder.exists.return_value = True
    folder.iterdir.return_value = [item]
    item.is_file.return_value = False
    item.is_symlink.return_value = False
    item.is_dir.return_value = True
    cleaner = Cleaner()
    item_checks = 0

    def becomes_reparse(path):
        nonlocal item_checks
        if path is not item:
            return False
        item_checks += 1
        return item_checks == 2

    rmtree_mock = Mock()
    monkeypatch.setattr("src.cleaner.is_trusted_cleanup_path", lambda *_: True)
    monkeypatch.setattr("src.cleaner.has_access", lambda *_: True)
    monkeypatch.setattr(cleaner, "_is_reparse_point", becomes_reparse)
    monkeypatch.setattr(cleaner, "get_directory_size", lambda *_: 100)
    monkeypatch.setattr("src.cleaner.shutil.rmtree", rmtree_mock)

    assert cleaner.clear_folder(folder, "Cache") == 0
    rmtree_mock.assert_not_called()


def test_clear_folder_counts_files_removed_before_directory_failure(monkeypatch):
    folder = Mock()
    item = Mock()
    folder.exists.return_value = True
    folder.iterdir.return_value = [item]
    item.is_file.return_value = False
    item.is_symlink.return_value = False
    item.is_dir.return_value = True
    item.exists.return_value = True
    cleaner = Cleaner()
    status_mock = Mock()
    sizes = iter((100, 40))
    monkeypatch.setattr("src.cleaner.is_trusted_cleanup_path", lambda *_: True)
    monkeypatch.setattr("src.cleaner.has_access", lambda *_: True)
    monkeypatch.setattr(cleaner, "_is_reparse_point", lambda *_: False)
    monkeypatch.setattr(cleaner, "get_directory_size", lambda *_: next(sizes))
    monkeypatch.setattr(
        "src.cleaner.shutil.rmtree", Mock(side_effect=PermissionError("locked"))
    )
    monkeypatch.setattr(cleaner, "print_status", status_mock)

    assert cleaner.clear_folder(folder, "Cache") == 60
    status_mock.assert_not_called()


def test_remove_safe_reparse_point_ignores_lstat_failure():
    path = Mock()
    path.lstat.side_effect = OSError("gone")

    assert Cleaner()._remove_safe_reparse_point(path) is None


def test_print_status_delegates_to_shared_utility(monkeypatch):
    status_mock = Mock()
    monkeypatch.setattr("src.cleaner.print_status", status_mock)

    Cleaner().print_status("message", error=True, emoji="[❗]")

    status_mock.assert_called_once_with("message", error=True, emoji="[❗]")


def test_get_local_drive_roots_filters_non_local_drives(monkeypatch):
    kernel32 = Mock()
    kernel32.GetLogicalDrives.return_value = (1 << 2) | (1 << 3) | (1 << 4)
    kernel32.GetDriveTypeW.side_effect = lambda root: {
        "C:\\": 3,
        "D:\\": 2,
        "E:\\": 4,
    }[root]
    monkeypatch.setattr(Cleaner, "_kernel32", lambda: kernel32)

    assert Cleaner.get_local_drive_roots() == ["C:\\", "D:\\"]


def test_get_local_drive_roots_reports_api_failure(monkeypatch):
    kernel32 = Mock()
    kernel32.GetLogicalDrives.return_value = 0
    monkeypatch.setattr(Cleaner, "_kernel32", lambda: kernel32)

    with pytest.raises(OSError, match="GetLogicalDrives"):
        Cleaner.get_local_drive_roots()


def test_recycle_bin_cleans_each_local_drive_and_reports_total(monkeypatch):
    shell32 = Mock()

    def query_drive(root, info_pointer):
        size, items = {"C:\\": (4096, 2), "D:\\": (2048, 1)}[root]
        info_pointer._obj.i64Size = size
        info_pointer._obj.i64NumItems = items
        return 0

    shell32.SHQueryRecycleBinW.side_effect = query_drive
    shell32.SHEmptyRecycleBinW.return_value = 0
    cleaner = Cleaner()
    monkeypatch.setattr(cleaner, "_shell32", lambda: shell32)
    monkeypatch.setattr(cleaner, "get_local_drive_roots", lambda: ["C:\\", "D:\\"])

    assert cleaner.clear_recycle_bin() == 6144
    flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
    assert shell32.SHEmptyRecycleBinW.call_args_list == [
        call(None, "C:\\", flags),
        call(None, "D:\\", flags),
    ]


def test_recycle_bin_dry_run_only_queries_each_drive(monkeypatch):
    shell32 = Mock()

    def query_drive(_root, info_pointer):
        info_pointer._obj.i64Size = 100
        return 0

    shell32.SHQueryRecycleBinW.side_effect = query_drive
    cleaner = Cleaner(dry_run=True)
    monkeypatch.setattr(cleaner, "_shell32", lambda: shell32)
    monkeypatch.setattr(cleaner, "get_local_drive_roots", lambda: ["C:\\", "D:\\"])

    assert cleaner.clear_recycle_bin() == 200
    shell32.SHEmptyRecycleBinW.assert_not_called()


def test_recycle_bin_continues_after_per_drive_failures(monkeypatch):
    shell32 = Mock()
    status_mock = Mock()

    def query_drive(root, info_pointer):
        if root == "E:\\":
            return -0x7FFF0001
        info_pointer._obj.i64Size = 4096 if root == "C:\\" else 2048
        info_pointer._obj.i64NumItems = 1
        return 0

    shell32.SHQueryRecycleBinW.side_effect = query_drive
    shell32.SHEmptyRecycleBinW.side_effect = (0, -0x7FFF0001)
    cleaner = Cleaner()
    monkeypatch.setattr(cleaner, "_shell32", lambda: shell32)
    monkeypatch.setattr(
        cleaner, "get_local_drive_roots", lambda: ["C:\\", "D:\\", "E:\\"]
    )
    monkeypatch.setattr(cleaner, "print_status", status_mock)

    assert cleaner.clear_recycle_bin() == 4096
    messages = [call.args[0] for call in status_mock.call_args_list]
    assert any("D:\\" in message and "0x8000FFFF" in message for message in messages)
    assert any("E:\\" in message and "0x8000FFFF" in message for message in messages)


def test_recycle_bin_raises_when_no_drive_can_be_inspected(monkeypatch):
    shell32 = Mock()
    shell32.SHQueryRecycleBinW.return_value = -0x7FFF0001
    cleaner = Cleaner()
    monkeypatch.setattr(cleaner, "_shell32", lambda: shell32)
    monkeypatch.setattr(cleaner, "get_local_drive_roots", lambda: ["C:\\"])
    monkeypatch.setattr(cleaner, "print_status", Mock())

    with pytest.raises(OSError, match="No local Recycle Bins"):
        cleaner.clear_recycle_bin()


def test_prepare_preset_uses_saved_choices_after_english_prompt(monkeypatch):
    choices = {DNS_CHOICE_KEY: True}
    store = Mock(load=Mock(return_value=choices), save=Mock(return_value=True))
    cleaner = Cleaner(preset_store=store)
    prompt_mock = Mock(return_value=True)
    monkeypatch.setattr("src.cleaner.get_yes_no", prompt_mock)
    monkeypatch.setattr(cleaner, "print_status", Mock())

    cleaner._prepare_preset()

    prompt_mock.assert_called_once_with("Use the last preset? (y/n): ")
    assert cleaner._use_preset is True
    assert cleaner._preset_choices == choices


def test_prepare_preset_starts_fresh_when_saved_preset_is_declined(monkeypatch):
    store = Mock(
        load=Mock(return_value={DNS_CHOICE_KEY: True}), save=Mock(return_value=True)
    )
    cleaner = Cleaner(preset_store=store)
    monkeypatch.setattr("src.cleaner.get_yes_no", lambda *_: False)

    cleaner._prepare_preset()

    assert cleaner._use_preset is False
    assert cleaner._preset_choices == {}


def test_choose_reuses_present_choice_and_prompts_for_new_target(monkeypatch):
    cleaner = Cleaner()
    cleaner._use_preset = True
    cleaner._preset_choices = {"known": False}
    confirmation = Mock(return_value=True)
    monkeypatch.setattr("src.cleaner.get_user_confirmation", confirmation)

    assert cleaner._choose("known", "Known", "Description") is False
    confirmation.assert_not_called()
    assert cleaner._choose("new", "New", "Description") is True
    assert cleaner._preset_choices["new"] is True


def test_save_preset_warns_without_stopping_cleanup(monkeypatch):
    store = Mock(load=Mock(return_value=None), save=Mock(return_value=False))
    cleaner = Cleaner(preset_store=store)
    status_mock = Mock()
    monkeypatch.setattr(cleaner, "print_status", status_mock)

    cleaner._save_preset()

    assert any(
        "Could not save" in call.args[0] and call.kwargs["error"] is True
        for call in status_mock.call_args_list
    )


def test_run_routes_recycle_bin_to_shell_api(monkeypatch):
    store = Mock(load=Mock(return_value=None), save=Mock(return_value=True))
    cleaner = Cleaner(preset_store=store)
    recycle_mock = Mock(return_value=1024)
    folder_mock = Mock(return_value=2048)
    monkeypatch.setattr(
        "src.cleaner.get_temp_dirs",
        lambda: [
            ("Recycle Bin", r"C:\\$Recycle.Bin", "all drives", False),
            ("Cache", r"C:\\Cache", "cache", False),
        ],
    )
    monkeypatch.setattr(cleaner, "clear_recycle_bin", recycle_mock)
    monkeypatch.setattr(cleaner, "clear_folder", folder_mock)
    monkeypatch.setattr(cleaner, "flush_dns", Mock())
    monkeypatch.setattr(cleaner, "print_status", Mock())
    monkeypatch.setattr("src.cleaner.get_user_confirmation", lambda *_: False)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    cleaner.run()

    recycle_mock.assert_called_once_with()
    folder_mock.assert_called_once()
    assert cleaner.total_deleted_size == 3072


def test_run_continues_when_recycle_bin_api_fails(monkeypatch):
    store = Mock(load=Mock(return_value=None), save=Mock(return_value=True))
    cleaner = Cleaner(preset_store=store)
    status_mock = Mock()
    monkeypatch.setattr(
        "src.cleaner.get_temp_dirs",
        lambda: [("Recycle Bin", r"C:\\$Recycle.Bin", "all drives", False)],
    )
    monkeypatch.setattr(
        cleaner, "clear_recycle_bin", Mock(side_effect=OSError("denied"))
    )
    monkeypatch.setattr(cleaner, "flush_dns", Mock())
    monkeypatch.setattr(cleaner, "print_status", status_mock)
    monkeypatch.setattr("src.cleaner.get_user_confirmation", lambda *_: False)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    cleaner.run()

    assert cleaner.total_deleted_size == 0
    assert any(
        "Failed to clean Recycle Bin" in call.args[0]
        for call in status_mock.call_args_list
    )
