import { useEffect, useRef, useState } from "react";

import {
  ApiError,
  createReading,
  drawCards,
  errorMessage,
  getInterpretation,
  getReading,
  interpretReading,
  listSpreads,
} from "./api";
import { Copy } from "./components/Copy";
import { ReadingTable } from "./components/ReadingTable";
import { SetupScreen } from "./components/SetupScreen";
import { clearSession, loadSession, saveSession } from "./session";
import type { DrawRequest, Interpretation, ReadingState, Spread } from "./types";

export function App() {
  const [spreads, setSpreads] = useState<Spread[] | null>(null);
  const [reading, setReading] = useState<ReadingState | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [interpretation, setInterpretation] = useState<Interpretation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      try {
        const catalog = await listSpreads();
        if (cancelled) {
          return;
        }
        setSpreads(catalog.spreads);
        const saved = loadSession();
        if (!saved) {
          return;
        }
        try {
          const state = await getReading(saved.readingId, saved.accessToken);
          if (cancelled) {
            return;
          }
          setToken(saved.accessToken);
          setReading(state);
          if (state.status === "completed") {
            await loadInterpretation(saved.readingId, saved.accessToken, cancelled);
          }
        } catch (caught) {
          clearSession();
          if (!cancelled) {
            setError(
              caught instanceof ApiError && caught.status === 401
                ? "先前的占卜憑證已失效，請重新開始。 The saved reading token is no longer valid. Start a new reading."
                : errorMessage(caught),
            );
          }
        }
      } catch (caught) {
        if (!cancelled) {
          setError(errorMessage(caught));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, []);

  async function loadInterpretation(readingId: string, accessToken: string, cancelled = false) {
    try {
      const existing = await getInterpretation(readingId, accessToken);
      if (!cancelled) {
        setInterpretation(existing);
      }
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 404) {
        return;
      }
      if (!cancelled) {
        setError(errorMessage(caught));
      }
    }
  }

  async function start(input: {
    question: string;
    spreadSlug: string;
    reversalsEnabled: boolean;
  }) {
    if (lock.current) {
      return;
    }
    lock.current = true;
    setBusy(true);
    setError(null);
    try {
      const created = await createReading({
        question: input.question,
        spread_slug: input.spreadSlug,
        reversals_enabled: input.reversalsEnabled,
      });
      saveSession({
        readingId: created.reading_id,
        accessToken: created.access_token,
      });
      setToken(created.access_token);
      setInterpretation(null);
      setReading(created);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  async function draw(body: DrawRequest) {
    if (!reading || !token || lock.current) {
      return;
    }
    lock.current = true;
    setBusy(true);
    setError(null);
    try {
      await drawCards(reading.reading_id, token, body, crypto.randomUUID());
      const next = await getReading(reading.reading_id, token);
      setReading(next);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  async function interpret() {
    if (!reading || !token || lock.current) {
      return;
    }
    lock.current = true;
    setBusy(true);
    setError(null);
    try {
      const result = await interpretReading(
        reading.reading_id,
        token,
        crypto.randomUUID(),
      );
      setInterpretation(result);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  function reset() {
    if (
      reading &&
      reading.status !== "completed" &&
      !window.confirm(
        "重新開始會留下這一局，但這個瀏覽器將無法再打開它。要繼續嗎？\nStarting over leaves this reading on the server, but this browser will not be able to open it again. Continue?",
      )
    ) {
      return;
    }
    clearSession();
    setReading(null);
    setToken(null);
    setInterpretation(null);
    setError(null);
  }

  return (
    <div className="app">
      <header className="masthead">
        <p className="mark">78</p>
        <div>
          <h1>一副牌，一次洗牌</h1>
          <p className="en title-en">One deck, shuffled once</p>
          <p>
            <Copy
              zh="七十八張牌在開始時排好，正逆位也在那時決定。點選牌背只是翻開已經放好的那一張。"
              en="All 78 cards are ordered when the reading starts, and each orientation is fixed then. Choosing a card back only reveals the card already waiting there."
            />
          </p>
        </div>
      </header>

      {error ? <p className="error banner-error">{error}</p> : null}

      {loading ? (
        <p className="quiet center">
          <Copy zh="正在連接牌桌…" en="Connecting to the table…" />
        </p>
      ) : null}

      {!loading && !reading && spreads ? (
        <SetupScreen spreads={spreads} busy={busy} onStart={(input) => void start(input)} />
      ) : null}

      {!loading && !reading && !spreads ? (
        <p className="quiet center">
          <Copy
            zh="後端還沒有回應。在 backend 目錄執行 uvicorn 後重新整理。"
            en="The API has not responded. Start uvicorn from the backend directory, then refresh."
          />
        </p>
      ) : null}

      {reading ? (
        <ReadingTable
          key={reading.reading_id}
          reading={reading}
          interpretation={interpretation}
          busy={busy}
          onDraw={(body) => void draw(body)}
          onInterpret={() => void interpret()}
          onReset={reset}
        />
      ) : null}
    </div>
  );
}
