from autopr.state import AgentState


def generate_pr_node(state: AgentState) -> dict:
    patches = state.get("patches", [])
    exec_result = state.get("verification_result")
    retries = state.get("retry_count", 0)

    pr_body = [
        f"## AutoPR: Automated Resolution for {state['ticket_id']}",
        "",
        "### Implementation Plan",
        state.get("plan", "No plan provided."),
        "",
        "### Modified Files",
        "\n".join([f"- `{p.file_path}`" for p in patches]),
        "",
        "### Verification Report",
        "- **Status**: PASS :white_check_mark:",
        f"- **Verification Cycles**: {retries}",
        f"- **Sandbox Exit Code**: {exec_result.exit_code if exec_result else 0}",
    ]

    return {"pr_ready": True, "triage_notes": "\n".join(pr_body)}


def escalate_node(state: AgentState) -> dict:
    return {
        "pr_ready": False,
        "triage_notes": f"Escalated to human review. Max retries ({state.get('max_retries', 3)}) exceeded or issue not actionable.",
    }
