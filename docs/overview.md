# Project Overview: AutoPR

**AutoPR** is an autonomous AI software engineering agent designed to resolve GitHub issue tickets and generate verified, production-ready Pull Requests. Built with [LangGraph](https://github.com/langchain-ai/langgraph) and powered by Google Gemini, AutoPR implements an iterative, self-correcting development loop rather than a naive one-shot code generator.

---

## 1. Motivation & Problem Statement

Standard LLM code assistants typically operate in a single-turn, unverified fashion: an issue description is fed in, and raw code snippets or diffs are output. This causes several critical pain points in real-world engineering workflows:

- **Hallucinated or Non-Compiling Code**: Unchecked code changes often break existing test suites or fail syntax parsing.
- **Context Overload & Irrelevant Snippets**: Ingesting entire codebases into LLM context windows degrades reasoning quality and increases token latency and costs.
- **Vague or Inactionable Issues**: Tickets that lack reproduction steps or clear requirements waste expensive model inference cycles.
- **Absence of Feedback Loops**: When a proposed code change fails tests, single-pass models cannot introspect the execution failure to iteratively repair the code.

AutoPR solves these problems by combining **structured issue triage**, **hybrid lexical-semantic code retrieval**, **isolated sandbox execution**, and **iterative test-driven repair loops**.

---

## 2. Core Capabilities

| Feature | Description |
|---|---|
| **Automated Triage** | Evaluates issue clarity and actionability upfront using Gemini structured generation (`TriageDecision`). Rejects underspecified tickets before executing code retrieval or synthesis. |
| **Hybrid Code Retrieval** | Combines AST-based Python code segmenting with sparse BM25 scoring (for exact symbol matches) and dense vector embeddings (for semantic meaning), blended via Reciprocal Rank Fusion (RRF, $k=60$). |
| **Solution Planning & Patch Generation** | Employs Gemini (`gemini-3.1-flash-lite`) to produce a coherent technical plan alongside complete, structured file patches (`FilePatch`). |
| **Isolated Sandbox Verification** | Replicates the workspace in an isolated ephemeral filesystem, applies patches, executes the test suite (`pytest`), enforces timeouts, and parses failing test identifiers. |
| **Self-Correcting Feedback Loop** | If sandbox verification fails, test traces, exit codes, failing test names, and stderr are fed back into subsequent planning and coding cycles until tests pass or the retry budget is exhausted. |
| **PR Synthesis & Human Escalation** | Constructs Markdown Pull Request descriptions with verification summaries upon success, or safely escalates to human engineers if the issue is rejected or max retries are reached. |

---

## 3. Technology Stack

- **Language & Runtime**: Python >= 3.12
- **Package & Virtual Environment Manager**: [uv](https://docs.astral.sh/uv/) with `uv_build` backend
- **Agent Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph) (StateGraph state machine)
- **Language Models**: Google Gemini via `langchain-google-genai` and `langchain-core` (default model: `gemini-3.1-flash-lite`)
- **Data Validation & Schemas**: [Pydantic v2](https://docs.pydantic.dev/)
- **Code Retrieval & Indexing**:
  - **AST Chunking**: Standard library `ast` module (`ASTCodeChunker`), `tree-sitter`, `tree-sitter-python`
  - **Dense Embeddings**: `sentence-transformers` (model: `BAAI/bge-small-en-v1.5`)
  - **Sparse Lexical Search**: `rank-bm25` (BM25Okapi)
  - **Vector Database**: `qdrant-client`
  - **Rank Blending**: Reciprocal Rank Fusion (RRF)
- **Sandbox Execution**: `docker`, `subprocess`, and isolated temporary workspaces
- **Testing**: `pytest`
