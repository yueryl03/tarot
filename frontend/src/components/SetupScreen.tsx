import { useState, type FormEvent } from "react";

import { Copy } from "./Copy";
import { spreadName } from "../labels";
import type { Spread } from "../types";

interface SetupScreenProps {
  spreads: Spread[];
  busy: boolean;
  onStart: (input: {
    question: string;
    spreadSlug: string;
    reversalsEnabled: boolean;
  }) => void;
}

export function SetupScreen({ spreads, busy, onStart }: SetupScreenProps) {
  const [question, setQuestion] = useState("");
  const [spreadSlug, setSpreadSlug] = useState(
    spreads.find((spread) => spread.slug === "past-present-future")?.slug ??
      spreads[0]?.slug ??
      "",
  );
  const [reversalsEnabled, setReversalsEnabled] = useState(true);
  const [localError, setLocalError] = useState<string | null>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      setLocalError("先寫下想問的事。 Write the question first.");
      return;
    }
    if (!spreadSlug) {
      setLocalError("請選擇一個牌陣。 Choose a spread.");
      return;
    }
    setLocalError(null);
    onStart({
      question: trimmed,
      spreadSlug,
      reversalsEnabled,
    });
  }

  return (
    <form className="setup" onSubmit={submit}>
      <label className="question-field">
        <span>
          想問的事
          <span className="en">Your question</span>
        </span>
        <textarea
          value={question}
          maxLength={2000}
          rows={4}
          placeholder="例如：這段關係現在需要我看見什麼？  e.g. What should I see in this relationship?"
          onChange={(event) => setQuestion(event.target.value)}
        />
      </label>

      <fieldset className="spread-picker">
        <legend>
          牌陣
          <span className="en">Spread</span>
        </legend>
        <div className="spread-options">
          {spreads.map((spread) => (
            <label key={spread.slug} className={spread.slug === spreadSlug ? "is-chosen" : ""}>
              <input
                type="radio"
                name="spread"
                value={spread.slug}
                checked={spread.slug === spreadSlug}
                onChange={() => setSpreadSlug(spread.slug)}
              />
              <strong>{spreadName(spread)}</strong>
              <em className="en">{spread.name}</em>
              <em>
                {spread.card_count} 張 · {spread.card_count}{" "}
                {spread.card_count === 1 ? "card" : "cards"}
              </em>
              <span>{spread.description}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <label className="reversal-toggle">
        <input
          type="checkbox"
          checked={reversalsEnabled}
          onChange={(event) => setReversalsEnabled(event.target.checked)}
        />
        <span>
          <Copy
            zh="允許逆位。洗牌時每張牌各自有一半的機會逆位，翻開時不再重抽。"
            en="Allow reversals. During the shuffle, each card is independently reversed with probability 1/2. Turning a card does not roll again."
          />
        </span>
      </label>

      {localError ? <p className="error">{localError}</p> : null}

      <button className="primary" type="submit" disabled={busy}>
        {busy ? (
          <Copy zh="正在洗牌…" en="Shuffling…" />
        ) : (
          <Copy zh="洗牌並開始" en="Shuffle and begin" />
        )}
      </button>
    </form>
  );
}
