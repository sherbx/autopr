import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


class HybridCodeRetriever:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.embedding_model = SentenceTransformer(model_name)
        self.chunks = []
        self.bm25 = None
        self.corpus_embeddings = None

    def index_chunks(self, chunks: list[dict]):
        """
        chunks: List of dicts with keys: {'id': str, 'content': str, 'metadata': dict}
        """
        self.chunks = chunks
        tokenized_corpus = [chunk["content"].lower().split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Precompute dense embeddings
        texts = [chunk["content"] for chunk in chunks]
        self.corpus_embeddings = self.embedding_model.encode(
            texts, normalize_embeddings=True
        )

    def _reciprocal_rank_fusion(
        self, sparse_ranked: list[str], dense_ranked: list[str], k: int = 60
    ) -> list[tuple[str, float]]:
        scores: dict[str, float] = {}
        for rank, doc_id in enumerate(sparse_ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        for rank, doc_id in enumerate(dense_ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self.bm25 is None or not self.chunks:
            return []

        # 1. Sparse BM25 ranking
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        sparse_indices = np.argsort(bm25_scores)[::-1]
        sparse_ranked_ids = [self.chunks[i]["id"] for i in sparse_indices]

        # 2. Dense semantic ranking (Cosine similarity via dot product on normalized vectors)
        query_embedding = self.embedding_model.encode(
            [query], normalize_embeddings=True
        )[0]
        dense_scores = np.dot(self.corpus_embeddings, query_embedding)
        dense_indices = np.argsort(dense_scores)[::-1]
        dense_ranked_ids = [self.chunks[i]["id"] for i in dense_indices]

        # 3. Fuse rankings via RRF
        fused = self._reciprocal_rank_fusion(sparse_ranked_ids, dense_ranked_ids)
        top_ids = [doc_id for doc_id, _ in fused[:top_k]]

        # Map back to full chunk payload
        chunk_map = {c["id"]: c for c in self.chunks}
        return [chunk_map[cid] for cid in top_ids]
