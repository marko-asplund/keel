from typing import TypedDict

import chromadb
from llama_index.core import (
    VectorStoreIndex,
)
from llama_index.core.vector_stores import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # pyright: ignore[reportMissingTypeStubs]
from llama_index.vector_stores.chroma import ChromaVectorStore  # pyright: ignore[reportMissingTypeStubs]


class RetrievedPassage(TypedDict):
    text: str
    fiscal_year: int | None
    source: str | None
    score: float | None


class FilingRetriever:
    DB_PATH: str = "./data/chroma"
    COLLECTION_NAME: str = "msft_filings"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    MAX_RESULTS: int = 3

    def __init__(self):
        db = chromadb.PersistentClient(path=self.DB_PATH)
        collection = db.get_collection(self.COLLECTION_NAME)

        vector_store = ChromaVectorStore(chroma_collection=collection)

        embed_model = HuggingFaceEmbedding(model_name=self.EMBEDDING_MODEL_NAME)

        self._index: VectorStoreIndex = VectorStoreIndex.from_vector_store(  # pyright: ignore[reportUnknownMemberType]
            vector_store,
            embed_model=embed_model,
        )

    async def retrieve(
        self, query: str, years: list[int]
    ) -> list[RetrievedPassage]:
        filters = MetadataFilters(
            filters=[
                MetadataFilter(
                    key="fiscal_year", operator=FilterOperator.IN, value=years
                ),
            ]
        )
        retriever = self._index.as_retriever(
            similarity_top_k=self.MAX_RESULTS, filters=filters
        )
        results = await retriever.aretrieve(query)
        return [
            {
                "text": r.node.get_content(),
                "fiscal_year": r.node.metadata.get("fiscal_year"),
                "source": r.node.metadata.get("file_name"),
                "score": r.score,
            }
            for r in results
        ]
