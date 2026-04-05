# Conversational AI Shopping Assistant Backend

Python FastAPI backend prototype for a conversational shopping assistant that uses Chroma for vector search, `sentence-transformers` for embeddings, and the Groq API for conversational responses and recommendation explanations.

## Features

- FastAPI backend only
- Chroma vector database with persistent local storage
- Product ingestion from JSON seed data
- Semantic product search
- Conversational recommendations with basic conversation memory
- Explanation endpoint for recommendation reasoning

## Project Structure

```text
app/
  api/
  core/
  models/
  services/
  main.py
data/
  products.json
  users.json
  purchase_history.json
storage/
  chroma/
```

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root if you want Groq-backed responses:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-8b-8192
```

If `GROQ_API_KEY` is not set, the app still runs locally and falls back to template-based responses for `/chat` and `/explain`.

## Run the Server

```bash
uvicorn app.main:app --reload
```

Once the server starts, open `http://127.0.0.1:8000/` for the basic prototype UI or `http://127.0.0.1:8000/docs` for Swagger.

## API Endpoints

- `GET /`
- `GET /health`
- `GET /users`
- `POST /ingest-products`
- `POST /search`
- `POST /chat`
- `POST /explain`

## Example Requests

### Search

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"kurta for beach wedding\"}"
```

### Chat

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"U001\", \"message\": \"I need something for a beach wedding\"}"
```

### Explain

```bash
curl -X POST http://127.0.0.1:8000/explain \
  -H "Content-Type: application/json" \
  -d "{\"product_id\": \"P001\", \"query\": \"beach wedding\"}"
```
