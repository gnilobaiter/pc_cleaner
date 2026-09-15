import runpy
from unittest.mock import Mock

import pytest


def test_main_exits_with_cli_result(monkeypatch):
    start_cli = Mock(return_value=7)
    monkeypatch.setattr("src.cli.start_cli", start_cli)

    with pytest.raises(SystemExit) as exit_result:
        runpy.run_path("main.py", run_name="__main__")

    assert exit_result.value.code == 7
    start_cli.assert_called_once_with()
