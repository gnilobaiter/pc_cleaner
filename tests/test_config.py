from src import config


def test_get_temp_dirs_uses_environment_values(monkeypatch):
    monkeypatch.setenv("SystemRoot", r"D:\\Windows")
    monkeypatch.setenv("SystemDrive", "D:")
    monkeypatch.setenv("USERPROFILE", r"D:\\Users\\Tester")
    monkeypatch.setenv("LOCALAPPDATA", r"D:\\Users\\Tester\\AppData\\Local")
    monkeypatch.setenv("APPDATA", r"D:\\Users\\Tester\\AppData\\Roaming")
    monkeypatch.setenv("PROGRAMDATA", r"D:\\ProgramData")

    directories = config.get_temp_dirs()

    assert directories
    assert all(len(entry) == 4 for entry in directories)
    assert all(isinstance(entry[3], bool) for entry in directories)
    assert any(name == "System Temp" and path == r"D:\\Windows\Temp" for name, path, _, _ in directories)
    assert any(name == "Recycle Bin" and path == r"D:$Recycle.Bin" for name, path, _, _ in directories)
    assert any(name == "VS Code Logs" and path.endswith(r"Code\logs") for name, path, _, _ in directories)


def test_get_temp_dirs_has_confirmed_and_unconfirmed_entries():
    directories = config.get_temp_dirs()

    assert any(needs_confirmation for _, _, _, needs_confirmation in directories)
    assert any(not needs_confirmation for _, _, _, needs_confirmation in directories)
    assert len({(name, path) for name, path, _, _ in directories}) == len(directories)
