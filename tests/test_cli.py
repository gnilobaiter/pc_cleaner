from unittest.mock import Mock

from src import cli


def test_start_cli_returns_zero_after_success(monkeypatch):
    cleaner = Mock(run=Mock(return_value=None))
    monkeypatch.setattr(cli, "Cleaner", lambda **_: cleaner)
    banner_mock = Mock()
    monkeypatch.setattr(cli, "print_banner", banner_mock)

    assert cli.start_cli() == 0
    banner_mock.assert_called_once_with()
    cleaner.run.assert_called_once_with()


def test_start_cli_handles_keyboard_interrupt(monkeypatch):
    cleaner = Mock(run=Mock(side_effect=KeyboardInterrupt))
    monkeypatch.setattr(cli, "Cleaner", lambda **_: cleaner)

    assert cli.start_cli() == 1
    cleaner.print_status.assert_called_once_with("Stopped by user", error=True)


def test_start_cli_handles_unexpected_error(monkeypatch):
    cleaner = Mock(run=Mock(side_effect=RuntimeError("boom")))
    monkeypatch.setattr(cli, "Cleaner", lambda **_: cleaner)

    assert cli.start_cli() == 1
    assert "Something broke: boom" in cleaner.print_status.call_args.args[0]
