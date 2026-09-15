from unittest.mock import Mock

import pytest

from src import utils


@pytest.mark.parametrize(
    ("size", "expected"),
    [(0, "0 B"), (1, "1.00 B"), (1024, "1.00 KB"), (1024**2, "1.00 MB"), (1024**4, "1.00 TB")],
)
def test_convert_size(size, expected):
    assert utils.convert_size(size) == expected


def test_has_access_requires_existing_readable_and_writable_path(monkeypatch, tmp_path):
    assert utils.has_access(tmp_path)
    assert not utils.has_access(tmp_path / "missing")

    monkeypatch.setattr(utils.os, "access", lambda *_: False)
    assert not utils.has_access(tmp_path)


def test_print_status_uses_fallback_without_colors(monkeypatch, capsys):
    monkeypatch.setattr(utils, "USE_COLORS", False)
    monkeypatch.setattr(utils, "_SUPPORTS_EMOJI", False)
    error_emoji = next(emoji for emoji, fallback in utils._EMOJI_FALLBACKS.items() if fallback == "[!]")

    utils.print_status("failed", error=True, emoji=error_emoji)

    assert "[!] failed" in capsys.readouterr().out


def test_print_status_uses_colors_when_enabled(monkeypatch, capsys):
    monkeypatch.setattr(utils, "USE_COLORS", True)
    monkeypatch.setattr(utils, "_SUPPORTS_EMOJI", True)
    monkeypatch.setattr(utils, "Fore", Mock(GREEN="green", YELLOW="yellow", CYAN="cyan", RED="red", MAGENTA="magenta"))
    monkeypatch.setattr(utils, "Style", Mock(RESET_ALL="reset"))

    success_emoji = next(emoji for emoji, fallback in utils._EMOJI_FALLBACKS.items() if fallback == "[+]")
    utils.print_status("done", emoji=success_emoji)

    output = capsys.readouterr().out
    assert "green" in output
    assert "done" in output
    assert "reset" in output


def test_print_banner_without_colors(monkeypatch, capsys):
    monkeypatch.setattr(utils, "USE_COLORS", False)

    utils.print_banner()

    output = capsys.readouterr().out
    assert f"PC_CLEANER {utils.VERSION}" in output
    assert "----" in output


@pytest.mark.parametrize("answers, expected", [(["Y"], True), (["n"], False), (["wrong", "y"], True)])
def test_get_user_confirmation_retries_until_valid(monkeypatch, answers, expected):
    input_mock = Mock(side_effect=answers)
    status_mock = Mock()
    monkeypatch.setattr(utils, "input", input_mock, raising=False)
    monkeypatch.setattr(utils, "print_status", status_mock)
    monkeypatch.setattr(utils, "USE_COLORS", False)

    assert utils.get_user_confirmation("Cache", "Description") is expected
    assert input_mock.call_count == len(answers)
    if len(answers) > 1:
        assert any(
            call.args[0] == "Please enter 'y' or 'n'" and call.kwargs["error"] is True
            for call in status_mock.call_args_list
        )
