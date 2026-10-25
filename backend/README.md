# Tarot reading backend

A modular monolith for an AI-assisted Rider-Waite-Smith reading. The tarot engine shuffles and reveals a physical 78-card deck. The interpretation layer only reads a finished reading; it cannot choose cards, orientations, or positions.

Upright and reversed are orientations of the same card. The database stores 78 cards, not 156.

## Shuffle model

Each new reading builds one deck and stores it before any card is shown.

1. Fisher-Yates shuffles the 78 card ids. The random source is `secrets.SystemRandom.randrange`, the same unbiased generator `secrets.randbelow` uses. The Python `random` module is not used.
2. When reversals are enabled, every card then gets its own `randbelow(2)`. `1` is reversed and `0` is upright, so each orientation has probability 1/2. These calls are independent of each other and of the card's identity.
3. When reversals are disabled, every card is upright and the orientation bit is not drawn.
4. Slots `0` through `77` are inserted in one transaction. Slot `0` is the top of the deck. Database triggers keep the slot count at 78, refuse a reversed card when reversals are off, and reject later changes to card, slot, or orientation.

Before any card is revealed:

- `P(a specific card is the top card) = 1/78`
- the same probability holds for any fixed slot, because the permutation is uniform
- with reversals enabled, `P(a specific card with a specified orientation) = 1/156` for that first card

After `k` cards have been revealed, `78 - k` cards remain. The next top card is uniform among the remaining slots. Its orientation is the value stored at shuffle time. Revealing a card does not roll again, and a reading is never reshuffled.

This is an idealised model of a physical shuffle. A person shuffling real cards does not necessarily produce a perfectly uniform order or a perfectly fair share of reversals.

Two readings call the random source separately, so their decks are independent.

## Layout

```text
backend/
  app/
    main.py
    core/                 configuration, token hashing, JSON logs
    domain/               shuffle, draw planning, errors (no FastAPI, SQLAlchemy, or AI)
    db/                   session, 78-card catalog, spreads, seed
    models/               SQLAlchemy models
    repositories/
    services/             reading lifecycle and the engine facade
    ai/                   provider interface, mock, OpenAI-compatible adapter
    api/v1/               HTTP routes
    schemas/
  alembic/
  tests/
  scripts/shuffle_simulation.py
  Dockerfile
  docker-compose.yml
```

Tests live in `backend/tests` rather than inside the application package so pytest does not import them as part of the service.

## Database

| Table | Role |
| --- | --- |
| `tarot_cards` | 78 unique cards. Major arcana are `canonical_number` 0–21 (Strength 8, Justice 11). |
| `tarot_meanings` | One upright row and one reversed row per card. Unique `(card_id, orientation)`. |
| `tarot_spreads` | Spread name, slug, and `card_count`. |
| `tarot_spread_positions` | Position index, name, and description. Unique `(spread_id, position_index)`. |
| `reading_sessions` | Question, spread, status, reversal flag, SHA-256 token hash. |
| `reading_deck_slots` | The shuffled deck. Unique `(reading_id, slot_index)` and `(reading_id, card_id)`. |
| `reading_draws` | A revealed slot assigned to one spread position. A slot and a position can each be used once. |
| `interpretations` | Provider output. Writing one does not update the deck. |
| `idempotency_keys` | Replay of a draw or interpret retry. The raw reading token is not stored here. |

Statuses are `created`, `in_progress`, and `completed`. The reading becomes `completed` in the same transaction as the draw that fills the spread.

Seed meanings are original development text. Every general meaning starts with "Development seed meaning, not a licensed or proprietary source". They are not a licensed deck book. Replace `app/db/card_catalog.py` (`meanings_for`) or update `tarot_meanings` and run the seed again. Card identity does not depend on that text.

Add a spread by editing `app/db/spread_catalog.py` and re-seeding. The draw planner only reads `card_count` and assigns positions in the order the cards are revealed.

## Security

`POST /api/v1/readings` returns `access_token` once. PostgreSQL stores `sha256(token)` in hex. Later calls send `Authorization: Bearer <access_token>`. The UUID in the URL is an identifier, not a credential. Logs redact bearer tokens and do not record the question or the raw token.

There is no list-all-readings endpoint. A response never includes an unrevealed card id, name, orientation, or image key. It does include the indexes of slots that have already been turned.

Creating a reading is not idempotent. Replaying that response would require storing the raw token, which this service does not do. If the create response is lost, that reading cannot be opened. Draws and interpretations accept `Idempotency-Key`. The same key and body return the original result and do not consume more cards. The same key with a different body returns `409 idempotency_conflict`.

CORS origins come from `CORS_ORIGINS`. No API key is hardcoded. `INTERPRETATION_API_KEY` is optional and is only sent to an OpenAI-compatible base URL when that provider is selected.

## API

Prefix: `/api/v1`. Interactive docs: `http://localhost:8000/docs`.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | no | Process is up. |
| `GET` | `/health/ready` | no | Database answers `SELECT 1`. |
| `GET` | `/api/v1/cards` | no | 78-card catalog and seed meanings. |
| `GET` | `/api/v1/spreads` | no | Spreads and positions. |
| `POST` | `/api/v1/readings` | no | Shuffle a new deck. Returns the token once. |
| `GET` | `/api/v1/readings/{id}` | bearer | State, revealed cards, open positions. |
| `POST` | `/api/v1/readings/{id}/draw` | bearer | Reveal from the top or by slot. |
| `GET` | `/api/v1/readings/{id}/draws` | bearer | Cards revealed so far. |
| `POST` | `/api/v1/readings/{id}/interpret` | bearer | Interpret a completed reading. |
| `GET` | `/api/v1/readings/{id}/interpretation` | bearer | Latest stored interpretation. |

Errors use one envelope:

```json
{"error": {"code": "slot_already_revealed", "message": "...", "details": {}}}
```

Draw modes:

```json
{"mode": "top", "count": 3}
```

```json
{"mode": "select", "slot_indices": [12, 40, 7]}
```

`top` reveals the lowest remaining slot indexes. `select` reveals those slots in the order given. Positions are assigned in that same reveal order: the first card of the reading is position `0`. A failed batch inserts nothing. The draw response lists only the cards revealed by that request. `revealed_slot_indices` lists every turned slot, sorted, and does not include hidden identities.

Built-in spreads: `single-card`, `past-present-future`, `five-card`, `celtic-cross`.

The default interpreter is `MockInterpretationProvider`. Its text is marked `DEMONSTRATION ONLY` and is a deterministic rendering of the stored cards and seed meanings. It is not a language-model reading. Set `INTERPRETATION_PROVIDER=openai_compatible` plus `INTERPRETATION_BASE_URL` and `INTERPRETATION_MODEL` to call a Chat Completions endpoint such as vLLM. That adapter is not used for shuffling. The prompt tells the model that the cards are already chosen and that the reading is symbolic, not a verified prediction or a fact about another person.

## Local setup

From `backend/`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

Start PostgreSQL. With Docker:

```bash
docker compose up -d db
```

The compose file creates user `tarot`, password `tarot`, database `tarot`, and publishes port `5432`.

Without Docker, create the same role and database, then:

```bash
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or start the API in Docker as well. The API container migrates and seeds on startup:

```bash
docker compose up --build
```

Open `http://localhost:8000/docs`.

The reading UI is in `frontend/`. It proxies `/api` to this server, so start the API first:

```bash
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The page keeps the reading token in `localStorage`, so a refresh returns to the same deck. Closing the browser after choosing “重新開始”, or clearing site data, drops the only copy of the token.

Create a reading:

```bash
curl -s -X POST http://localhost:8000/api/v1/readings \
  -H 'Content-Type: application/json' \
  -d '{"question":"What should I know about my relationship?","spread_slug":"past-present-future","reversals_enabled":true}'
```

The response includes `reading_id` and `access_token`. It does not include card names.

Select three face-down slots:

```bash
curl -s -X POST "http://localhost:8000/api/v1/readings/$READING_ID/draw" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"mode":"select","slot_indices":[12,40,7]}'
```

Drawing three cards completes `past-present-future`. Fetch it again after a refresh:

```bash
curl -s "http://localhost:8000/api/v1/readings/$READING_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Interpret the completed reading:

```bash
curl -s -X POST "http://localhost:8000/api/v1/readings/$READING_ID/interpret" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Run the tests:

```bash
pytest
```

Integration tests use `TAROT_TEST_DATABASE_URL` or `postgresql+asyncpg://tarot:tarot@localhost:5432/tarot_test`. The database name must contain `test`. They migrate, seed, and truncate reading rows between tests. Catalog rows stay in place.

The default pytest run skips the large frequency sample (`-m 'not statistical'`). To run it:

```bash
pytest -m statistical
python -m scripts.shuffle_simulation --shuffles 20000
```

The script prints how often each card appears in slot 0, the upright/reversed split, and the mean number of reversed cards per reading. It fails if those fall outside a wide tolerance. A few dozen decks are not used as a fairness assertion in ordinary CI.

## Tests

Unit tests cover the permutation, scripted orientations, draw planning, token hashing, log redaction, the mock provider, and the OpenAI-compatible request builder.

Integration tests cover a 78-card persisted deck, no duplicate draws, rejected repeat slots, spread limits, completion, reload after a new request, invalid spreads and slots, concurrent draws, unauthorized access, interpretation leaving the deck unchanged, idempotent seeding, response keys, a failed batch that consumes nothing, and idempotency keys.

## Limitations

- Anonymous sessions only. A lost create response cannot be recovered, because the raw token is not stored.
- Create is not idempotent, for the same reason.
- The shuffle is uniform. It does not imitate the bias of a human riffle or the way a person reverses cards.
- Seed meanings are placeholders, not a curated traditional text.
- The mock interpreter is deterministic demonstration text.
- The OpenAI-compatible adapter is off unless configured. This phase does not train a LoRA or retrieve from a vector index. The provider interface is the extension point: pass the question, spread, revealed cards, orientations, positions, and database meanings. The provider does not get a database session.
- No card image files are served. `image_key` is a stable lookup key such as `rws/major/00-the-fool`.
- Rate limiting and user accounts are out of scope. Draw safety across API workers comes from `SELECT ... FOR UPDATE` on the reading row.
