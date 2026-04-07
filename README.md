# yonder-ai-interviewer
Building a POC for an AI Interviewer solution.

## Docker

Set `OPENAI_API_KEY` in a local `.env` file, then build and run with Docker Compose.

Build the image:

```bash
docker compose build
```

Start the web app:

```bash
docker compose up web
```

Run the CLI app:

```bash
docker compose run --rm cli
```

Persistent app data is stored in:

- `./data` for SQLite databases
- `./results` for exported transcripts
