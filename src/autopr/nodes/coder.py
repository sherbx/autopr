from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from autopr.state import AgentState, FilePatch


class CodePlanAndPatch(BaseModel):
    plan: str = Field(description="Detailed explanation of the technical changes made.")
    patches: list[FilePatch] = Field(
        description="List of files and their updated complete source code.",
    )


CODER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer. Your task is to write complete, clean code fixes "
            "to resolve the specified issue. Adhere strictly to the existing codebase patterns.\n"
            "Always provide the full updated file contents for modified files.",
        ),
        (
            "human",
            "### Issue: {ticket_id}\n"
            "{description}\n\n"
            "### Retrieved Codebase Context:\n"
            "{context}\n\n"
            "### Previous Attempt Failure (if any):\n"
            "{failure_context}\n\n"
            "Generate a plan and the exact file replacements to resolve the issue.",
        ),
    ],
)


def plan_and_code_node(state: AgentState, llm: ChatGoogleGenerativeAI = None) -> dict:
    """Plans and generates code fixes for an issue ticket."""
    if llm is None:
        llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.1)

    structured_llm = llm.with_structured_output(CodePlanAndPatch)
    chain = CODER_PROMPT | structured_llm

    # Format previous execution failure if we are in a retry cycle
    failure_context = "No previous failures. This is the first attempt."
    last_exec = state.get("verification_result")
    if last_exec and not last_exec.passed:
        failure_context = (
            f"Exit Code: {last_exec.exit_code}\n"
            f"Failing Tests: {', '.join(last_exec.failing_test_names)}\n"
            f"Error Details / Stderr:\n{last_exec.stderr or last_exec.stdout}"
        )

    docs_joined = "\n\n---\n\n".join(state.get("retrieved_docs", []))

    result: CodePlanAndPatch = chain.invoke(
        {
            "ticket_id": state["ticket_id"],
            "description": state["issue_description"],
            "context": docs_joined if docs_joined else "No context retrieved.",
            "failure_context": failure_context,
        },
    )

    return {"plan": result.plan, "patches": result.patches}
