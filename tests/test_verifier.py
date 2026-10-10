from pathlib import Path

import pytest

from autopr.state import FilePatch
from autopr.tools.sandbox import SandboxExecutionEngine


@pytest.fixture
def mock_repo(tmp_path: Path):
    """Creates a temporary mock repo containing a sample module and pytest suite."""
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    # Target module
    module = repo / "calculator.py"
    module.write_text("def add(a, b):\n    return a + b\n")

    # Test file
    test_file = repo / "test_calculator.py"
    test_file.write_text(
        "from calculator import add\n"
        "def test_add():\n"
        "    assert add(2, 3) == 5\n"
        "def test_broken():\n"
        "    assert add(1, 1) == 2\n"
    )
    return repo


def test_sandbox_executes_passing_code(mock_repo):
    engine = SandboxExecutionEngine(base_repo_path=str(mock_repo))
    result = engine.execute_in_isolated_env(patches=[])

    assert result.passed is True
    assert result.exit_code == 0
    assert len(result.failing_test_names) == 0


def test_sandbox_catches_buggy_patch(mock_repo):
    engine = SandboxExecutionEngine(base_repo_path=str(mock_repo))

    # Introduce a buggy patch that breaks the calculation
    broken_patch = FilePatch(
        file_path="calculator.py", diff="def add(a, b):\n    return a - b\n"
    )

    result = engine.execute_in_isolated_env(patches=[broken_patch])

    assert result.passed is False
    assert result.exit_code != 0
    assert any("test_add" in name for name in result.failing_test_names)


def test_sandbox_enforces_timeout(mock_repo):
    engine = SandboxExecutionEngine(base_repo_path=str(mock_repo), timeout_seconds=1)

    # Introduce an infinite loop patch
    infinite_loop_patch = FilePatch(
        file_path="calculator.py",
        diff="import time\ndef add(a, b):\n    while True:\n        time.sleep(0.1)\n",
    )

    result = engine.execute_in_isolated_env(patches=[infinite_loop_patch])

    assert result.passed is False
    assert "timed out" in result.stderr
