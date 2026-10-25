# Tarot reading frontend

A small React app for the reading API in `../backend`.

The page asks for a question and a spread, then shows the 78 face-down slots from that reading. Choosing slots calls `mode: "select"`. Drawing from the top calls `mode: "top"`. The browser never receives an unrevealed card. When the spread is full, it can ask the API for the mock interpretation.

The reading id and bearer token are stored in `localStorage` so a refresh reloads the same deck. The API only returns the token once.

## Run

Start the API on port 8000, then:

```bash
npm install
npm run dev
```

Open http://localhost:3000. Vite proxies `/api` to `http://127.0.0.1:8000`.

Set `VITE_API_BASE` if the API is on another origin, and include that origin in the API `CORS_ORIGINS`.
