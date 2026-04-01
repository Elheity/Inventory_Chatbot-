## Setup

### 1. Install dependencies
```bash
pip install openai pydantic
```

### 2. Configure environment
Edit the `.env` file and set your API key (already pre-configured for OpenAI):
```
PROVIDER=openai
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o
PORT=8000
```

To use **Azure OpenAI** instead:
```
PROVIDER=azure
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=
```

### 3. Run the server
```bash
cd .../ChatAssgiment
python server.py
```

### 4. Open the UI
Visit: [http://localhost:8000](http://localhost:8000)

## API Reference

### `POST /api/chat`
**Request:**
```json
{
  "session_id": "abc123",
  "message": "How many assets do I have?",
  "context": {}
}
```

**Response:**
```json
{
  "answer": "You currently have 19 active assets across all your sites.",
  "query": "SELECT COUNT(*) AS AssetCount FROM Assets WHERE Status <> 'Disposed';",
  "suggested_questions": [
    "Which site has the most assets?",
    "What is the total value of assets?",
    "How many assets are in repair?"
  ],
  "token_usage": { "prompt_tokens": 1420, "completion_tokens": 180, "total_tokens": 1600 },
  "latency_ms": 1340,
  "provider": "openai",
  "model": "gpt-4o",
  "status": "ok"
}
```

### `POST /api/session/clear`
```json
{ "session_id": "abc123" }
```

## Project Structure
```
ChatAssgiment/
├── server.py      # HTTP server (built-in http.server)
├── llm.py         # OpenAI integration + session management
├── database.py    # SQLite schema + sample data + query executor
├── prompt.py      # System prompt builder (schema + data as knowledge base)
├── models.py      # Pydantic request/response models
├── index.html     # Web chat UI
├── .env           # Environment variables
└── README.md
```
