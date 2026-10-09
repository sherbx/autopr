from autopr.graph import AgentState
from autopr.retrieval.hybrid_search import HybridCodeRetriever

# Module-level or injected retriever instance
retriever = HybridCodeRetriever()


def retrieve_context_node(state: AgentState) -> dict:
    query = f"{state['ticket_id']}: {state['issue_description']}"

    # Retrieve top relevant code chunks
    matched_chunks = retriever.search(query=query, top_k=4)

    formatted_context = [
        f"File: {c['metadata']['file_path']} (lines {c['metadata']['start_line']}-{c['metadata']['end_line']})\n"
        f"Symbol: {c['metadata']['symbol_name']}\n"
        f"```\n{c['content']}\n```"
        for c in matched_chunks
    ]

    return {"retrieved_docs": formatted_context}
