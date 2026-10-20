# Run manually to index HTML financial filings from data/documents into Chroma.

from pathlib import Path
from typing import cast

import chromadb
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding  # pyright: ignore[reportMissingTypeStubs]
from llama_index.readers.file import HTMLTagReader  # pyright: ignore[reportMissingTypeStubs]
from llama_index.vector_stores.chroma import ChromaVectorStore  # pyright: ignore[reportMissingTypeStubs]

if Path("data/chroma/chroma.sqlite3").exists():
    raise SystemExit(
        "Chroma RAG database already exists. Delete data/chroma/ before reindexing."
    )

# Local embedding model
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Persistent Chroma database
db = chromadb.PersistentClient(path="./data/chroma")
collection = db.create_collection("msft_filings")

vector_store = ChromaVectorStore(chroma_collection=collection)

# Initialize the index backed by Chroma
index = VectorStoreIndex.from_vector_store(  # pyright: ignore[reportUnknownMemberType]
    vector_store,
    embed_model=embed_model,
)

# Load and index documents incrementally
reader = SimpleDirectoryReader(
    input_dir="data/documents",
    required_exts=[".html"],
    file_extractor={".html": HTMLTagReader(tag="body")},
)

for documents in reader.iter_data():
    for document in documents:
        filename = cast(str, document.metadata["file_name"])
        document.metadata["fiscal_year"] = int(filename.split("-")[1])

        index.insert(document)
        print(f"Indexed {filename}")

print(f"Indexed {collection.count()} chunks")
