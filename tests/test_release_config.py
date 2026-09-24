import re
from pathlib import Path


def test_release_actions_are_pinned_to_full_commit_hashes():
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")
    action_refs = re.findall(r"^\s*uses:\s*([^\s#]+)", workflow, re.MULTILINE)

    assert action_refs
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref) for ref in action_refs)


def test_release_requires_tests_and_coverage_gate():
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "needs: [check-commit-message, tests]" in workflow
    assert "--cov-fail-under=95" in workflow
