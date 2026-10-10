# AutoPR - Agent Project Memory & Guidelines

## 1. Project Overview
`autopr` is an autonomous AI agent engineered to resolve GitHub issues and generate production-ready Pull Requests. Built using **LangGraph**, it runs an iterative cycle of triage, hybrid code retrieval, solution planning, code patching, and sandbox verification.

---

## 2. Tech Stack & Environment
- **Language**: Python >= 3.12 (see [.python-version](file:///home/sherby/development/portfolio/ai/autopr/.python-version))
- **Package & Environment Manager**: [uv](https://docs.astral.sh/uv/) with `uv_build` backend
- **Agent Orchestration**: `langgraph>=1.2.14`
- **LLM & Structured Generation**: `langchain-google-genai>=4.4.1`, `langchain-core>=1.6.9` (default model: `gemini-3.1-flash-lite`)
- **Data Validation & Schemas**: `pydantic>=2.14.0`
- **Retrieval & Indexing**:
  - **AST Chunking**: Python standard `ast` module (`ASTCodeChunker`), `tree-sitter>=0.26.0`, `tree-sitter-python>=0.25.0`
  - **Dense Embeddings**: `sentence-transformers>=6.1.0` (default model: `BAAI/bge-small-en-v1.5`)
  - **Sparse Search**: `rank-bm25>=0.2.2`
  - **Vector Database**: `qdrant-client>=1.19.1`
  - **Rank Fusion**: Reciprocal Rank Fusion (RRF)
- **Sandbox & Execution**: `docker>=7.2.0`, ephemeral isolated filesystem environments
- **Testing**: `pytest>=9.1.1`

---

## 3. Architecture & Agent Workflow

### Graph Lifecycle
The workflow is orchestrated via `StateGraph(AgentState)` in [src/autopr/graph.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/graph.py):

```
[triage_node]
     │
     ├── (is_actionable == False) ──────> [escalate_node] ──> END
     │
     └── (is_actionable == True)
              │
              ▼
   [retrieve_context_node]
              │
              ▼
     [plan_and_code_node] <──────────────┐ (retries < max_retries
              │                          │  and verification failed)
              ▼                          │
  [sandbox_verification_node] ───────────┘
              │
              ├── (passed == True) ──────> [generate_pr_node] ──> END
              │
              └── (retry limit reached) ─> [escalate_node] ──> END
```

### Core Components
- **State Definition** ([src/autopr/state.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/state.py)):
  - `AgentState`: TypedDict containing ticket details, triage flags, retry counts, retrieved docs, generated patches, and verification results. Always import from `autopr.state` (never `autopr.graph`).
  - `FilePatch`: Pydantic model for target file paths and replacement source code/diffs.
  - `ExecutionResult`: Pydantic model for test status (`passed`), exit code, stdout, stderr, and parsed failing test names.
- **Triage Node** ([src/autopr/nodes/triage.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/nodes/triage.py)):
  - Evaluates issue descriptions via structured Gemini calls (`TriageDecision`) to decide if a ticket is actionable.
- **Context Retrieval Node** ([src/autopr/nodes/context.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/nodes/context.py)):
  - Queries `HybridCodeRetriever` using the ticket query and stores formatted source snippets in `retrieved_docs`.
- **Solution Planning & Coding Node** ([src/autopr/nodes/coder.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/nodes/coder.py)):
  - Formulates an engineering plan and concrete file patches (`CodePlanAndPatch`).
  - Incorporates previous sandbox execution failures (exit codes, failing test names, stderr/stdout) during retry loops.
- **Sandbox Execution & Verification** ([src/autopr/nodes/verifier.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/nodes/verifier.py) & [src/autopr/tools/sandbox.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/tools/sandbox.py)):
  - `SandboxExecutionEngine`: Creates ephemeral workspace replicas, applies `FilePatch` diffs, executes test commands with timeout enforcement, and parses failing pytest identifiers.
  - `sandbox_verification_node`: Updates `verification_result` and increments `retry_count`.
- **PR Generation & Escalation** ([src/autopr/nodes/pr.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/nodes/pr.py)):
  - `generate_pr_node`: Constructs markdown PR summaries with status, verification cycles, and modified files.
  - `escalate_node`: Flags non-actionable or exhausted retry tickets for human engineer review.
- **AST Chunking** ([src/autopr/retrieval/ast_chunker.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/retrieval/ast_chunker.py)):
  - Parses Python code into structured `CodeChunk` dataclasses capturing symbol names, chunk types (function, class), start/end lines, and source code.
- **Hybrid Retrieval** ([src/autopr/retrieval/hybrid_search.py](file:///home/sherby/development/portfolio/ai/autopr/src/autopr/retrieval/hybrid_search.py)):
  - Combines BM25 token-level scoring (exact identifiers) with cosine similarity of dense embeddings (semantic meaning).
  - Uses Reciprocal Rank Fusion (RRF, $k=60$) to blend ranked lists.

---

## 4. Directory Structure
```
autopr/
├── src/
│   └── autopr/
│       ├── __init__.py
│       ├── graph.py                 # LangGraph state machine & routers
│       ├── state.py                 # AgentState and Pydantic schemas
│       ├── nodes/                   # Graph execution nodes
│       │   ├── __init__.py
│       │   ├── context.py           # Context retrieval node
│       │   ├── triage.py            # Issue triage & validation node
│       │   ├── coder.py             # Solution planning & code patching
│       │   ├── verifier.py          # Sandbox test execution
│       │   └── pr.py                # Pull request generator & escalation
│       ├── retrieval/               # Code search & indexing
│       │   ├── ast_chunker.py       # AST-based code segmenter
│       │   └── hybrid_search.py     # Hybrid BM25 + dense search retriever
│       └── tools/                   # Agent tool integrations
│           ├── __init__.py
│           └── sandbox.py           # Test execution sandbox runner
├── tests/
│   ├── test_agent_loop.py           # Agent coder feedback loop unit tests
│   ├── test_context_node.py         # Unit tests for context retrieval node
│   ├── test_retrieval.py            # AST chunker and hybrid search tests
│   └── test_verifier.py             # Sandbox execution and timeout tests
├── pyproject.toml                   # Project metadata and dependencies
└── uv.lock                          # Dependency lockfile
```

---

## 5. Development & Testing Commands
All commands should be executed via `uv`:

- **Run all tests**:
  ```bash
  uv run pytest
  ```

- **Run a specific test file**:
  ```bash
  uv run pytest tests/test_retrieval.py
  ```

- **Run with stdout enabled**:
  ```bash
  uv run pytest -s
  ```

- **Add a dependency**:
  ```bash
  uv add <package-name>
  ```

- **Add a development dependency**:
  ```bash
  uv add --dev <package-name>
  ```

- **Sync dependencies**:
  ```bash
  uv sync
  ```

---

## 6. Coding Standards & Agent Guidelines
1. **Node Conventions**:
   - Every LangGraph node should accept `AgentState` (or a subset) and return a dictionary update for the state.
   - Do not mutate input state directly; return updates.
2. **Type Safety & State Imports**:
   - Always provide strict type annotations across functions and classes.
   - Use Pydantic models for structured entities and validation.
   - **Always import `AgentState` from `autopr.state`** (never from `autopr.graph`) to prevent circular dependencies during module loading.
3. **Retrieval & Testing Best Practices**:
   - When writing unit tests for nodes that use retrievers or external embedding models, mock or monkeypatch `HybridCodeRetriever.search` (as in [tests/test_context_node.py](file:///home/sherby/development/portfolio/ai/autopr/tests/test_context_node.py)) to avoid downloading heavy weights or running unnecessary inference during CI.
   - When testing nodes using LangChain LCEL pipelines (`PROMPT | structured_llm`), ensure mocks configure both `.return_value` and `.invoke.return_value`, and inspect prompt values passed downstream.
4. **Preserve Comments & Docstrings**:
   - Maintain existing docstrings and comments when modifying code.
