from autopr.state import AgentState, ExecutionResult
from autopr.tools.sandbox import SandboxExecutionEngine


def sandbox_verification_node(state: AgentState) -> dict:
    repo_path = state.get("target_repo_path", "./")
    patches = state.get("patches", [])
    current_retry = state.get("retry_count", 0)

    runner = SandboxExecutionEngine(base_repo_path=repo_path, timeout_seconds=45)

    # Run test verification
    exec_result: ExecutionResult = runner.execute_in_isolated_env(
        patches=patches,
        test_command="pytest -q",
    )

    return {"verification_result": exec_result, "retry_count": current_retry + 1}
