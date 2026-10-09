import pytest

from autopr.retrieval.ast_chunker import ASTCodeChunker
from autopr.retrieval.hybrid_search import HybridCodeRetriever

# Sample codebase fixture representing typical backend modules
SAMPLE_AUTH_CODE = """
AUTH_SESSION_EXPIRED_CODE = "ERR_AUTH_901"

class SessionManager:
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl

    def invalidate_token(self, token_id: str) -> bool:
        \"\"\"Revokes active credentials and wipes local session state.\"\"\"
        return True

def handle_user_login(user_id: str, secret: str):
    if not secret:
        raise ValueError("Secret cannot be empty")
    return {"status": "authenticated"}
"""

SAMPLE_PAYMENT_CODE = """
class StripeWebhookHandler:
    def process_charge_succeeded(self, event_payload: dict):
        \"\"\"Handles billing events and updates invoice records.\"\"\"
        invoice_id = event_payload.get("invoice_id")
        return {"processed": invoice_id}
"""


def test_ast_chunker_extracts_functions_and_classes():
    chunks = ASTCodeChunker.chunk_python_file(
        file_path="auth/session.py", source_code=SAMPLE_AUTH_CODE
    )

    # Should extract: SessionManager (class), handle_user_login (function)
    symbols = [c.symbol_name for c in chunks]
    assert "SessionManager" in symbols
    assert "handle_user_login" in symbols

    # Verify line numbers are captured
    class_chunk = next(c for c in chunks if c.symbol_name == "SessionManager")
    assert class_chunk.start_line == 4
    assert "invalidate_token" in class_chunk.content


@pytest.fixture(scope="module")
def populated_retriever():
    retriever = HybridCodeRetriever()

    auth_chunks = ASTCodeChunker.chunk_python_file("auth/session.py", SAMPLE_AUTH_CODE)
    payment_chunks = ASTCodeChunker.chunk_python_file(
        "billing/stripe.py", SAMPLE_PAYMENT_CODE
    )

    all_chunks = []
    for idx, c in enumerate(auth_chunks + payment_chunks):
        all_chunks.append(
            {
                "id": f"chunk_{idx}",
                "content": c.content,
                "metadata": {
                    "file_path": c.file_path,
                    "symbol_name": c.symbol_name,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                },
            }
        )

    retriever.index_chunks(all_chunks)
    return retriever


def test_exact_identifier_match_sparse(populated_retriever):
    """BM25 test: Exact variable or function name lookup."""
    results = populated_retriever.search("handle_user_login", top_k=1)

    assert len(results) > 0
    top_result = results[0]
    assert top_result["metadata"]["symbol_name"] == "handle_user_login"
    assert top_result["metadata"]["file_path"] == "auth/session.py"


def test_semantic_match_dense(populated_retriever):
    """Dense test: Conceptual query with zero keyword overlap."""
    # "revoke credentials" doesn't appear explicitly in the query
    results = populated_retriever.search(
        "where do we revoke active credentials and drop user state", top_k=1
    )

    assert len(results) > 0
    top_result = results[0]
    assert top_result["metadata"]["symbol_name"] == "SessionManager"
    assert "invalidate_token" in top_result["content"]
