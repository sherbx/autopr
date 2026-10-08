import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field


class FilePatch(BaseModel):
    file_path: str = Field(description="Target file relative path")
    diff: str = Field(description="Unified git diff or complete file contents")


class ExecutionResult(BaseModel):
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    failing_test_names: list[str] = Field(default_factory=list)


class AgentState(TypedDict):
    # Input
    ticket_id: str
    issue_description: str
    target_repo_path: str

    # Workflow controls
    is_actionable: bool
    triage_notes: str
    retry_count: int
    max_retries: int

    # Context & Planning
    retrieved_docs: Annotated[list[str], operator.add]
    plan: str | None

    # Code artifacts
    patches: list[FilePatch]
    verification_result: ExecutionResult | None
    pr_ready: bool
