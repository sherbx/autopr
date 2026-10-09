from langgraph.graph import END, StateGraph

from autopr.state import AgentState


# Node stubs (to be populated in subsequent milestones)
def triage_node(_state: AgentState) -> dict:
    return {"is_actionable": True, "triage_notes": "Issue spec is complete."}


def retrieve_context_node(_state: AgentState) -> dict:
    return {"retrieved_docs": ["Relevant source file and interface specs."]}


def plan_and_code_node(_state: AgentState) -> dict:
    return {"plan": "1. Update schema. 2. Fix bug in handler.", "patches": []}


def sandbox_verification_node(state: AgentState) -> dict:
    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "verification_result": None,
    }


def generate_pr_node(_state: AgentState) -> dict:
    return {"pr_ready": True}


def escalate_node(_state: AgentState) -> dict:
    return {"pr_ready": False}


# Conditional Routers
def route_triage(state: AgentState) -> str:
    if state.get("is_actionable", False):
        return "retrieve_context_node"
    return "escalate_node"


def route_verification(state: AgentState) -> str:
    result = state.get("verification_result")
    retries = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if result and result.passed:
        return "generate_pr_node"

    if retries < max_retries:
        return "plan_and_code_node"

    return "escalate_node"


workflow = StateGraph(AgentState)
workflow.add_node("triage_node", triage_node)
workflow.add_node("retrieve_context_node", retrieve_context_node)
workflow.add_node("plan_and_code_node", plan_and_code_node)
workflow.add_node("sandbox_verification_node", sandbox_verification_node)
workflow.add_node("generate_pr_node", generate_pr_node)
workflow.add_node("escalate_node", escalate_node)

workflow.set_entry_point("triage_node")

workflow.add_conditional_edges("triage_node", route_triage)
workflow.add_edge("retrieve_context_node", "plan_and_code_node")
workflow.add_edge("plan_and_code_node", "sandbox_verification_node")
workflow.add_conditional_edges("sandbox_verification_node", route_verification)
workflow.add_edge("generate_pr_node", END)
workflow.add_edge("escalate_node", END)

app = workflow.compile()
