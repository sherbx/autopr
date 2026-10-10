from autopr.nodes.context import retrieve_context_node
from autopr.state import AgentState


def test_retrieve_context_node_populates_state(monkeypatch) -> None:
    mock_results = [
        {
            "content": "def login(): pass",
            "metadata": {
                "file_path": "auth.py",
                "start_line": 1,
                "end_line": 2,
                "symbol_name": "login",
            },
        }
    ]
    monkeypatch.setattr(
        "autopr.nodes.context.retriever.search",
        lambda query, top_k=4: mock_results,
    )

    test_state: AgentState = {
        "ticket_id": "ENG-402",
        "issue_description": "User login fails when secret is omitted",
        "target_repo_path": "/tmp/repo",
        "is_actionable": True,
        "triage_notes": "",
        "retry_count": 0,
        "max_retries": 3,
        "retrieved_docs": [],
        "plan": None,
        "patches": [],
        "verification_result": None,
        "pr_ready": False,
    }

    result = retrieve_context_node(test_state)
    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) == 1
