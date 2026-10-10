# AutoPR Documentation

Welcome to the AutoPR documentation library. Here you will find guides on what AutoPR is, how to install and execute it, and how its internal systems and state machine are designed.

---

## Documentation Sections

1. [**Project Overview**](file:///home/sherby/development/portfolio/ai/autopr/docs/overview.md)
   - What is AutoPR?
   - Motivation and pain points addressed
   - Core capabilities and feature matrix
   - Technology stack and dependency breakdown

2. [**Getting Started & Usage**](file:///home/sherby/development/portfolio/ai/autopr/docs/getting-started.md)
   - Prerequisites and installation via `uv`
   - Setting up environment credentials (`GOOGLE_API_KEY`)
   - How to run AutoPR via Python API
   - Interpreting state inputs and outputs
   - Running the test suite (`uv run pytest`)

3. [**Architecture & System Design**](file:///home/sherby/development/portfolio/ai/autopr/docs/architecture.md)
   - LangGraph State Machine lifecycle and routing rules
   - Node-by-node specifications (`triage`, `context`, `coder`, `verifier`, `pr`, `escalate`)
   - Hybrid retrieval engine (AST chunking, BM25, dense embeddings, Reciprocal Rank Fusion)
   - Isolated sandbox verification runner and failure feedback loop
   - Data models and schema definitions (`AgentState`, `FilePatch`, `ExecutionResult`)
