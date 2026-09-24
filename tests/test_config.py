from types import SimpleNamespace

import pytest

from src import config


def test_get_temp_dirs_skips_untrusted_environment_roots(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"D:\\Windows")
    monkeypatch.setenv("SystemDrive", "D:")
    monkeypatch.setenv("USERPROFILE", r"D:\\Users\\Tester")
    monkeypatch.setenv("LOCALAPPDATA", r"D:\\Users\\Tester\\AppData\\Local")
    monkeypatch.setenv("APPDATA", r"D:\\Users\\Tester\\AppData\\Roaming")
    monkeypatch.setenv("PROGRAMDATA", r"D:\\ProgramData")

    directories = config.get_temp_dirs()

    assert directories == []


def test_get_temp_dirs_has_confirmed_and_unconfirmed_entries():
    directories = config.get_temp_dirs()

    assert any(needs_confirmation for _, _, _, needs_confirmation in directories)
    assert any(not needs_confirmation for _, _, _, needs_confirmation in directories)
    assert len({(name, path) for name, path, _, _ in directories}) == len(directories)


def test_destructive_system_targets_require_confirmation():
    directories = {
        name: needs_confirmation
        for name, _, _, needs_confirmation in config.get_temp_dirs()
    }

    assert directories["Live Kernel Reports"] is True
    assert directories["Event Logs"] is True
    assert directories["Windows.old"] is True


def test_cleanup_list_is_grouped_in_logical_order():
    names = [name for name, *_ in config.get_temp_dirs()]

    assert names.index("System Temp") < names.index("User Temp")
    assert names.index("User Temp") < names.index("Edge Cache")
    assert names.index("Edge Cache") < names.index("Pytest Cache")
    assert names.index("Pytest Cache") < names.index("Discord Cache")
    assert names.index("Discord Cache") < names.index("Steam HTML Cache")
    assert names.index("Steam HTML Cache") < names.index("Direct3D Shader Cache")


def test_new_cleanup_candidates_have_safe_confirmation_defaults():
    directories = {
        name: needs_confirmation
        for name, _, _, needs_confirmation in config.get_temp_dirs()
    }

    assert directories["NuGet HTTP Cache"] is False
    assert directories["NuGet Plugins Cache"] is False
    assert directories["Go Build Cache"] is True
    assert directories["Cargo Registry Cache"] is True
    assert directories["Opera Cache"] is True
    assert directories["System Error Reporting"] is True


def test_matching_entries_only_returns_existing_directories(tmp_path):
    cache = tmp_path / "Product2026.2" / "caches"
    cache.mkdir(parents=True)
    (tmp_path / "Product2025.1" / "caches.txt").parent.mkdir()

    entries = config._matching_entries(
        "IDE Cache", str(tmp_path), "*/caches", "description", True
    )

    assert entries == [("IDE Cache", str(cache), "description", True)]

    distinguished = config._matching_entries(
        "IDE Cache", str(tmp_path), "*/caches", "description", True, True
    )
    assert distinguished[0][0] == "IDE Cache (Product2026.2)"


def test_version_is_v1_2_0():
    assert config.VERSION == "v1.2.0"


def test_matching_entries_returns_empty_without_base():
    assert config._matching_entries("Cache", "", "*", "description", False) == []


def test_trusted_path_skips_empty_roots_and_cross_drive_errors(monkeypatch):
    monkeypatch.setattr(config, "_windows_directory", lambda: r"C:\Windows")
    monkeypatch.setattr(config, "get_trusted_roots", lambda: ("", r"D:\Allowed"))

    assert config.is_trusted_cleanup_path(r"C:\Untrusted") is False


def test_known_folder_and_windows_directory_failures_raise(monkeypatch):
    monkeypatch.setattr(
        config.ctypes.windll.kernel32,
        "GetWindowsDirectoryW",
        lambda *_: 0,
    )
    with pytest.raises(OSError, match="Windows directory"):
        config._windows_directory()

    monkeypatch.setattr(
        config.ctypes.windll.shell32,
        "SHGetFolderPathW",
        lambda *_: 1,
    )
    with pytest.raises(OSError, match="known folder"):
        config._known_folder(0x1A, "APPDATA")


def test_reparse_free_path_rejects_reparse_ancestor(monkeypatch):
    def fake_lstat(path):
        attributes = (
            config.stat.FILE_ATTRIBUTE_REPARSE_POINT if path.name == "junction" else 0
        )
        return SimpleNamespace(st_file_attributes=attributes)

    monkeypatch.setattr(config.Path, "lstat", fake_lstat)
    monkeypatch.setattr(config.Path, "is_symlink", lambda *_: False)

    assert (
        config.is_reparse_free_path(r"C:\Trusted\junction\cache", r"C:\Trusted")
        is False
    )


def test_reparse_free_path_rejects_paths_outside_root():
    assert config.is_reparse_free_path(r"D:\Elsewhere", r"C:\Trusted") is False
