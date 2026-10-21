# Keel

A learning project for modern Python async backend development. It implements
a small async Python wrapper API on top of Mistral's Chat Completions HTTP API.

- Supports multiturn chat by preserving conversation history between turns.
- Implements basic tool calling: registers Python functions with tool schemas,
  executes requested functions, and sends their results back to Mistral to
  continue the conversation.
- Retrieves and normalizes historical public-company revenue and operating
  income from SEC EDGAR.
- Uses that data to answer natural-language finance questions.

The goal is to learn how async API clients, chat state, and external data
sources work together in a Python backend.

## Quick setup

With uv installed, run these commands from the project root (Python 3.12 is
selected by `.python-version`):

```sh
uv sync

# Work around NLTK rejecting hard-linked LlamaIndex data files.
UV_LINK_MODE=copy uv sync --reinstall-package llama-index-core
```

Create a `.env` file containing your Mistral API key and SEC contact details:

```dotenv
MISTRAL_API_KEY=your-api-key
EDGAR_API_USER_AGENT="Your Name your.email@example.com"
```

Download Microsoft's annual SEC filings into `data/documents` (filings are not
included in Git):

```sh
mkdir -p data/documents
uv run python -m scripts.get_sec_filings MSFT --year 2024 2025 2026 2023
```

Then manually build the Chroma index:

```sh
uv run python -m scripts.rag_index
```

To rebuild an existing index after changing the documents, delete `data/chroma/`
before running the indexer again.

Run the example chat:

```sh
uv run python -m app.main
```
