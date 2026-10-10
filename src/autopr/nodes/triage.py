from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from autopr.state import AgentState


class TriageDecision(BaseModel):
    """Decides if an issue is actionable and provides notes on the decision."""

    is_actionable: bool = Field(
        description="True if the issue contains enough detail to reproduce and fix.",
    )
    notes: str = Field(
        description="Reasoning or missing information if not actionable.",
    )


TRIAGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an engineering triage lead. Analyze the issue ticket to determine if it "
            "describes a clear bug, feature, or reproduction path. If vague or missing critical context, reject it.",
        ),
        ("human", "Ticket ID: {ticket_id}\n\nDescription:\n{description}"),
    ],
)


def triage_node(state: AgentState) -> dict:
    """Triages an issue ticket to determine if it is actionable."""
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    structured_llm = llm.with_structured_output(TriageDecision)
    chain = TRIAGE_PROMPT | structured_llm

    decision: TriageDecision = chain.invoke(
        {"ticket_id": state["ticket_id"], "description": state["issue_description"]},
    )

    return {"is_actionable": decision.is_actionable, "triage_notes": decision.notes}
