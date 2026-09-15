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
