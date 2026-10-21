# Run manually to test semantic retrieval from the indexed financial filings.

import chromadb
from llama_index.core import (
    VectorStoreIndex,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # pyright: ignore[reportMissingTypeStubs]
from llama_index.vector_stores.chroma import ChromaVectorStore  # pyright: ignore[reportMissingTypeStubs]

db = chromadb.PersistentClient(path="./data/chroma")
collection = db.get_collection("sec_filings")

vector_store = ChromaVectorStore(chroma_collection=collection)

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

index = VectorStoreIndex.from_vector_store(  # pyright: ignore[reportUnknownMemberType]
    vector_store,
    embed_model=embed_model,
)

# Test semantic retrieval
retriever = index.as_retriever(similarity_top_k=3)
results = retriever.retrieve(
    "What risks does Microsoft identify related to artificial intelligence?"
)

for result in results:
    print("\n--- MATCH ---")
    print("Score:", result.score)
    print("Source:", result.node.metadata.get("file_name"))
    print("Ticker:", result.node.metadata.get("ticker"))
    print("Year:", result.node.metadata.get("fiscal_year"))
    print(result.node.get_content()[:1000])
