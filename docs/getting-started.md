# Getting Started with AutoPR

This guide walks through setting up your environment, configuring API credentials, and running the AutoPR autonomous agent workflow.

---

## 1. Prerequisites

Before running AutoPR, ensure your system meets the following requirements:

- **Python**: Version `3.12` or higher (verified via `.python-version`)
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (Astral's fast Python package manager)
- **Google Gemini API Key**: Access to Google AI Studio or Vertex AI Gemini models (`gemini-3.1-flash-lite`)
- **Docker** *(Optional)*: Required if executing tests inside containerized environments rather than local temporary directory sandboxes

---

## 2. Installation & Setup

### 2.1 Clone Repository & Install Dependencies

Clone the AutoPR repository and use `uv` to create a virtual environment and synchronize dependencies:

```bash
git clone https://github.com/sherbinator/autopr.git
cd autopr

# Synchronize all runtime and development dependencies
uv sync
```

### 2.2 Configure Environment Variables

AutoPR requires a Google Gemini API key to run LLM-powered triage, planning, and coding nodes. Set your key in your active environment:

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

You can verify the configuration:

```bash
uv run python -c "import os; assert 'GOOGLE_API_KEY' in os.environ, 'API key missing'"
```

---

## 3. How to Use AutoPR

### 3.1 Invoking the Agent via Python API

AutoPR compiles its agent workflow into a LangGraph `CompiledStateGraph` instance exposed as `app` in [`autopr.graph`](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/graph.py).

Here is a complete example of executing AutoPR against a target issue:

```python
from autopr.graph import app
from autopr.state import AgentState

# 1. Define the incoming issue ticket and configuration
initial_state: AgentState = {
    # Ticket inputs
    "ticket_id": "ENG-104",
    "issue_description": (
        "In calculator.py, function add(a, b) incorrectly subtracts when negative "
        "numbers are supplied. Ensure test_calculator passes."
    ),
    "target_repo_path": "./",  # Path to repository containing code & test suite

    # Workflow controls
    "is_actionable": False,
    "triage_notes": "",
    "retry_count": 0,
    "max_retries": 3,

    # Context & planning outputs
    "retrieved_docs": [],
    "plan": None,

    # Artifacts & verification
    "patches": [],
    "verification_result": None,
    "pr_ready": False,
}

# 2. Execute the autonomous agent loop
final_state = app.invoke(initial_state)

# 3. Inspect the execution outcome
if final_state.get("pr_ready"):
    print("=== Pull Request Ready ===")
    print(final_state.get("triage_notes"))  # Contains Markdown PR body
    print("\nGenerated Patches:")
    for patch in final_state.get("patches", []):
        print(f"File: {patch.file_path}")
        print(patch.diff)
else:
    print("=== Escalated to Human Review ===")
    print(final_state.get("triage_notes"))
```

### 3.2 Understanding Agent Outputs

When `app.invoke()` completes, `final_state` contains:

- **`pr_ready`** (`bool`): `True` if patches were synthesized and all test suite executions passed in the verification sandbox; `False` if escalated.
- **`patches`** (`list[FilePatch]`): List of target file paths and full replacement file contents.
- **`verification_result`** (`ExecutionResult`): Contains `passed`, `exit_code`, `stdout`, `stderr`, and `failing_test_names` from the final verification run.
- **`retry_count`** (`int`): Total number of sandbox execution iterations performed.
- **`triage_notes`** (`str`): Formatted Markdown PR description (on success) or explanation of why the ticket was rejected/escalated (on failure).

---

## 4. Running the Test Suite

All tests can be executed via `uv run pytest`:

```bash
# Run all unit tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with stdout output enabled
uv run pytest -s

# Run a specific test suite
uv run pytest tests/test_retrieval.py
uv run pytest tests/test_verifier.py
uv run pytest tests/test_agent_loop.py
uv run pytest tests/test_context_node.py
```

### Test Isolation Notice
Unit tests in `tests/` do not call live Google Gemini API endpoints or download transformer models over the network. External calls and embedding models are mocked to ensure instant, hermetic CI test execution.
