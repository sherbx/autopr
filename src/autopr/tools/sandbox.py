import shutil
import subprocess
import tempfile
from pathlib import Path

from autopr.state import ExecutionResult, FilePatch


class SandboxExecutionEngine:
    def __init__(self, base_repo_path: str, timeout_seconds: int = 30) -> None:
        self.base_repo_path = Path(base_repo_path)
        self.timeout_seconds = timeout_seconds

    def _apply_patches(self, target_dir: Path, patches: list[FilePatch]) -> None:
        """Overwrites or updates target files according to generated patches."""
        for patch in patches:
            target_file = target_dir / patch.file_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            # In complete file replacement mode:
            target_file.write_text(patch.diff, encoding="utf-8")

    def _parse_failing_tests(self, stdout: str) -> list[str]:
        """Extracts failing test node names from pytest output."""
        failing = []
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("FAILED ") and "::" in line:
                # pytest output: FAILED tests/test_auth.py::test_login - AssertionError
                parts = line.split()
                if len(parts) >= 2:
                    failing.append(parts[1])
        return failing

    def execute_in_isolated_env(
        self, patches: list[FilePatch], test_command: str = "pytest"
    ) -> ExecutionResult:
        """Creates an ephemeral copy of the repo, applies patches, and runs the test command with resource constraints."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "workspace"
            # 1. Clone workspace
            shutil.copytree(self.base_repo_path, temp_path)

            # 2. Apply patches
            self._apply_patches(temp_path, patches)

            # 3. Execute tests
            try:
                proc = subprocess.run(
                    test_command.split(),
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )
                stdout = proc.stdout
                stderr = proc.stderr
                exit_code = proc.returncode
            except subprocess.TimeoutExpired as e:
                return ExecutionResult(
                    passed=False,
                    exit_code=-1,
                    stdout=e.stdout or "",
                    stderr=f"Execution timed out after {self.timeout_seconds}s",
                    failing_test_names=[],
                )
            except Exception as e:
                return ExecutionResult(
                    passed=False,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    failing_test_names=[],
                )

            passed = exit_code == 0
            failing_tests = self._parse_failing_tests(stdout)

            return ExecutionResult(
                passed=passed,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                failing_test_names=failing_tests,
            )
