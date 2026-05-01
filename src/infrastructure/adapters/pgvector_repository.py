"""
PGVector Repository adapter.
Implements RepositoryPort for PostgreSQL with pgVector.
"""
from typing import List

from langchain_core.documents import Document as LangchainDocument
from langchain_postgres import PGVector
from sqlalchemy import text

from src.config.settings import get_settings
from src.domain.entities.document import DocumentChunk
from src.domain.ports.embeddings import EmbeddingsPort
from src.domain.ports.repository import RepositoryPort


class PGVectorRepository(RepositoryPort):
    """PostgreSQL with pgVector repository adapter."""
    
    def __init__(self, embeddings: EmbeddingsPort):
        self._settings = get_settings()
        self._embeddings = embeddings
        self._vectorstore = PGVector(
            collection_name=self._settings.pg_vector_collection_name,
            connection=self._settings.sqlalchemy_database_url,
            embeddings=embeddings.get_langchain_embeddings(),
        )
    
    def _reset_session(self) -> None:
        """Reset the vectorstore's scoped_session to avoid stale ORM state.

        Workaround for langchain-postgres scoped_session bug where
        the internal SQLAlchemy session accumulates stale ORM objects
        across calls, causing NotNullViolation on sequential inserts.
        """
        if hasattr(self._vectorstore, 'session_maker'):
            self._vectorstore.session_maker.remove()

    def add_documents(
        self,
        chunks: List[DocumentChunk],
        clear_existing: bool = False
    ) -> int:
        """Add document chunks to the repository."""
        # Convert to LangChain documents
        langchain_docs = [
            LangchainDocument(
                page_content=chunk.content,
                metadata=chunk.metadata
            )
            for chunk in chunks
        ]

        if clear_existing:
            self._vectorstore = PGVector.from_documents(
                documents=langchain_docs,
                embedding=self._embeddings.get_langchain_embeddings(),
                collection_name=self._settings.pg_vector_collection_name,
                connection=self._settings.sqlalchemy_database_url,
                pre_delete_collection=True,
            )
        else:
            # Clean session before insert to avoid stale state
            self._reset_session()
            self._vectorstore.add_documents(langchain_docs)

        return len(chunks)
    
    def search(self, query: str, k: int = 10) -> List[DocumentChunk]:
        """Search for similar documents using MMR for diversity."""
        results = self._vectorstore.max_marginal_relevance_search(
            query, k=k, fetch_k=k * 3
        )
        return [
            DocumentChunk(
                content=doc.page_content,
                metadata=doc.metadata
            )
            for doc in results
        ]
    
    def delete_by_source(self, source_file: str) -> int:
        """Delete all chunks from a specific source file."""
        engine = self._vectorstore._engine

        with engine.connect() as conn:
            # Get collection UUID
            result = conn.execute(
                text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
                {"name": self._settings.pg_vector_collection_name}
            )
            row = result.fetchone()
            if not row:
                return 0
            
            collection_uuid = row[0]
            
            # Delete embeddings where source_file matches
            result = conn.execute(
                text("""
                    DELETE FROM langchain_pg_embedding 
                    WHERE collection_id = :collection_id 
                    AND cmetadata->>'source_file' = :source_file
                """),
                {"collection_id": collection_uuid, "source_file": source_file}
            )
            conn.commit()
            
            return result.rowcount
    
    def get_retriever(self, k: int = 10):
        """Get a LangChain retriever using MMR for diversity."""
        return self._vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k, "fetch_k": k * 3},
        )
