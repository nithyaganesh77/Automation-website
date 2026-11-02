from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError:
    QdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None


class VectorStoreService:
    _client = None
    COLLECTION_NAME = "documind_documents"
    VECTOR_DIM = 384  # Standard MiniLM / Sentence Transformer dimension

    @classmethod
    def get_client(cls):
        if cls._client is None and QdrantClient:
            try:
                cls._client = QdrantClient(url=settings.QDRANT_URL, timeout=3.0)
                # Ensure collection exists
                collections = [c.name for c in cls._client.get_collections().collections]
                if cls.COLLECTION_NAME not in collections:
                    cls._client.create_collection(
                        collection_name=cls.COLLECTION_NAME,
                        vectors_config=VectorParams(size=cls.VECTOR_DIM, distance=Distance.COSINE),
                    )
            except Exception as e:
                logger.warning(f"Qdrant vector store connection skipped: {e}. Semantic vector indexing will run on-demand.")
                cls._client = None
        return cls._client

    @classmethod
    def index_document(cls, document_id: str, organization_id: str, text: str, metadata: Dict[str, Any] = None):
        """Indexes document text into Qdrant vector database."""
        client = cls.get_client()
        if not client:
            return False

        try:
            # Deterministic hash pseudo-embedding for local zero-dependency operation
            import hashlib
            h = hashlib.sha256(text.encode("utf-8")).digest()
            vector = [(float(b) / 255.0 - 0.5) for b in (h * 12)[:cls.VECTOR_DIM]]

            point = PointStruct(
                id=abs(hash(document_id)) % (2**63 - 1),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "organization_id": organization_id,
                    "snippet": text[:500],
                    **(metadata or {})
                }
            )
            client.upsert(collection_name=cls.COLLECTION_NAME, points=[point])
            return True
        except Exception as e:
            logger.warning(f"Failed to index point in Qdrant: {e}")
            return False
