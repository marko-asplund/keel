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
```

Create a `.env` file containing your Mistral API key:

```dotenv
MISTRAL_API_KEY=your-api-key
```

Set your SEC contact name and email in the `EdgarAPI(...)` call in `app/main.py`
(the example currently uses a hardcoded user agent), then run:

```sh
uv run python -m app.main
```
