# Gemini Agent Workspace Rules

Please refer to [AGENTS.md](file:///home/sherby/development/portfolio/ai/autopr/AGENTS.md) for the complete project memory, architectural diagrams, and component breakdowns.

## Key Rules & Guidelines

1. **Environment & Tooling**:
   - Python version: `>=3.12`.
   - Always run commands and tests via `uv run` (e.g., `uv run pytest`).
   - Use `uv add` or `uv sync` to manage project dependencies.

2. **Architecture**:
   - Built on **LangGraph** (`AgentState` defined in [src/autopr/state.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/state.py)).
   - Graph definition lives in [src/autopr/graph.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/graph.py).
   - Nodes must return dictionary updates to the state rather than mutating state in-place.

3. **Testing & Code Quality**:
   - Always keep unit tests fast and isolated. When testing nodes dependent on `HybridCodeRetriever`, mock or monkeypatch retriever calls to prevent downloading large transformer models in unit test runs.
   - Run `uv run pytest` to verify any modifications before concluding.
   - Maintain type annotations and documentation integrity.
