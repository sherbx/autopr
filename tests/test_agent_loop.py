from unittest.mock import MagicMock

from autopr.nodes.coder import CodePlanAndPatch, plan_and_code_node
from autopr.state import AgentState, FilePatch


def test_coder_node_receives_sandbox_feedback() -> None:
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    output = CodePlanAndPatch(
        plan="Fix off-by-one error",
        patches=[FilePatch(file_path="math.py", diff="def compute(): return 42")],
    )
    mock_structured.return_value = output
    mock_structured.invoke.return_value = output

    # State with simulated failed sandbox test run
    from autopr.state import ExecutionResult

    failing_state: AgentState = {
        "ticket_id": "ENG-101",
        "issue_description": "Fix bug in compute()",
        "target_repo_path": "./",
        "is_actionable": True,
        "triage_notes": "",
        "retry_count": 1,
        "max_retries": 3,
        "retrieved_docs": ["def compute(): return 0"],
        "plan": None,
        "patches": [],
        "verification_result": ExecutionResult(
            passed=False,
            exit_code=1,
            stdout="FAILED test_math.py::test_compute - AssertionError: assert 0 == 42",
            stderr="",
            failing_test_names=["test_math.py::test_compute"],
        ),
        "pr_ready": False,
    }

    result = plan_and_code_node(failing_state, llm=mock_llm)
    assert len(result["patches"]) == 1
    assert result["patches"][0].file_path == "math.py"

    # Confirm LLM received the failure trace
    call_args = (
        mock_structured.call_args[0][0]
        if mock_structured.call_args
        else mock_structured.invoke.call_args[0][0]
    )
    prompt_str = (
        call_args["failure_context"]
        if isinstance(call_args, dict) and "failure_context" in call_args
        else (
            call_args.to_string() if hasattr(call_args, "to_string") else str(call_args)
        )
    )
    assert "AssertionError: assert 0 == 42" in prompt_str
