import { useMemo } from "react";

import { Copy } from "./Copy";
import {
  orientationName,
  orientationNameEn,
  positionName,
  spreadName,
  statusName,
  statusNameEn,
  suitName,
  suitNameEn,
} from "../labels";
import type { DrawRequest, Interpretation, ReadingState } from "../types";

interface ReadingTableProps {
  reading: ReadingState;
  interpretation: Interpretation | null;
  busy: boolean;
  onDraw: (body: DrawRequest) => void;
  onInterpret: () => void;
  onReset: () => void;
}

const DECK_SIZE = 78;

export function ReadingTable({
  reading,
  interpretation,
  busy,
  onDraw,
  onInterpret,
  onReset,
}: ReadingTableProps) {
  const revealed = useMemo(
    () => new Set(reading.revealed_slot_indices),
    [reading.revealed_slot_indices],
  );
  const cardBySlot = useMemo(
    () => new Map(reading.draws.map((card) => [card.slot_index, card])),
    [reading.draws],
  );
  const remaining = reading.remaining_positions.length;
  const done = reading.status === "completed";
  const nextPosition = reading.remaining_positions[0] ?? null;

  function drawSlot(slot: number) {
    if (done || busy || revealed.has(slot) || remaining === 0) {
      return;
    }
    onDraw({ mode: "select", slot_indices: [slot] });
  }

  return (
    <section className="table">
      <div className="table-head">
        <div>
          <p className="eyebrow">
            {spreadName(reading.spread)} · {statusName(reading.status)}
            <span className="en">
              {reading.spread.name} · {statusNameEn(reading.status)}
            </span>
          </p>
          <h2>{reading.question}</h2>
          <p className="quiet">
            <Copy
              zh={
                reading.reversals_enabled
                  ? `逆位已在洗牌時決定。還剩 ${reading.available_count} 張蓋著的牌${
                      remaining > 0 ? `，牌陣還需要 ${remaining} 張` : "，牌陣已滿"
                    }。`
                  : `這一局全部正位。還剩 ${reading.available_count} 張蓋著的牌${
                      remaining > 0 ? `，牌陣還需要 ${remaining} 張` : "，牌陣已滿"
                    }。`
              }
              en={
                reading.reversals_enabled
                  ? `Reversals were fixed during the shuffle. ${reading.available_count} cards remain face down${
                      remaining > 0
                        ? `, and the spread still needs ${remaining}.`
                        : ", and the spread is full."
                    }`
                  : `Every card in this reading is upright. ${reading.available_count} cards remain face down${
                      remaining > 0
                        ? `, and the spread still needs ${remaining}.`
                        : ", and the spread is full."
                    }`
              }
            />
          </p>
        </div>
        <button className="ghost" type="button" onClick={onReset} disabled={busy}>
          <Copy zh="重新開始" en="Start over" />
        </button>
      </div>

      <SpreadSection reading={reading} nextIndex={nextPosition?.position_index ?? null} />

      {done ? null : (
        <div className="draw-bar">
          <p>
            <Copy
              zh="七十八張牌都蓋著。點一張就抽那一張，翻開後先顯示牌名。"
              en="All 78 cards stay face down. Click one to draw it. The face shows the card name."
            />
          </p>
        </div>
      )}

      <div className="fan">
        {Array.from({ length: DECK_SIZE }, (_, slot) => {
          const card = cardBySlot.get(slot);
          if (card) {
            const reversed = card.orientation === "reversed";
            return (
              <div
                key={slot}
                className={reversed ? "card-tile is-face is-reversed" : "card-tile is-face"}
              >
                <p className="tile-name">{card.card_name}</p>
                <p className="tile-orientation">
                  {orientationName(card.orientation)} / {orientationNameEn(card.orientation)}
                </p>
              </div>
            );
          }
          return (
            <button
              key={slot}
              type="button"
              className="card-tile is-back"
              disabled={done || busy || remaining === 0}
              aria-label={`第 ${slot + 1} 張牌背。 Card back ${slot + 1}.`}
              onClick={() => drawSlot(slot)}
            >
              <span className="back-pattern" />
            </button>
          );
        })}
      </div>

      {reading.draws.length > 0 ? (
        <ol className="draw-list">
          {reading.draws.map((card) => (
            <li key={card.slot_index}>
              <span>
                {card.draw_order}. {positionName(card.spread_position_name)}
              </span>
              <strong>{card.card_name}</strong>
              <em>
                {orientationName(card.orientation)} / {orientationNameEn(card.orientation)}
                {suitName(card.suit)
                  ? ` · ${suitName(card.suit)} / ${suitNameEn(card.suit)}`
                  : ""}
              </em>
              <p className="meaning">{card.general_meaning}</p>
            </li>
          ))}
        </ol>
      ) : null}

      {done ? (
        <InterpretationPanel
          interpretation={interpretation}
          busy={busy}
          onInterpret={onInterpret}
        />
      ) : null}
    </section>
  );
}

function SpreadSection({
  reading,
  nextIndex,
}: {
  reading: ReadingState;
  nextIndex: number | null;
}) {
  const byPosition = new Map(
    reading.draws.map((card) => [card.spread_position_index, card]),
  );
  if (reading.spread.slug === "celtic-cross") {
    return (
      <div className="celtic">
        {reading.spread.positions.map((position) => (
          <Slot
            key={position.position_index}
            name={position.name}
            description={position.description}
            card={byPosition.get(position.position_index)}
            isNext={position.position_index === nextIndex}
            area={CELTIC_AREA[position.position_index]}
            crossing={position.position_index === 1}
          />
        ))}
      </div>
    );
  }
  return (
    <ol className={`spread-row count-${reading.spread.card_count}`}>
      {reading.spread.positions.map((position) => (
        <li key={position.position_index}>
          <Slot
            name={position.name}
            description={position.description}
            card={byPosition.get(position.position_index)}
            isNext={position.position_index === nextIndex}
          />
        </li>
      ))}
    </ol>
  );
}

const CELTIC_AREA = [
  "present",
  "present",
  "foundation",
  "past",
  "crown",
  "near",
  "self",
  "environment",
  "hopes",
  "outcome",
];

function Slot({
  name,
  description,
  card,
  isNext,
  area,
  crossing = false,
}: {
  name: string;
  description: string;
  card: ReadingState["draws"][number] | undefined;
  isNext: boolean;
  area?: string;
  crossing?: boolean;
}) {
  return (
    <article
      className={[
        "position",
        card ? "is-filled" : "is-empty",
        isNext ? "is-next" : "",
        crossing ? "is-crossing" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={area ? { gridArea: area } : undefined}
      title={description}
    >
      <header>
        <span>
          {positionName(name)}
          {positionName(name) !== name ? <span className="en">{name}</span> : null}
        </span>
        {isNext && !card ? (
          <em>
            下一張<span className="en">Next</span>
          </em>
        ) : null}
      </header>
      <p className="position-note">{description}</p>
      {card ? (
        <div className={card.orientation === "reversed" ? "face is-reversed" : "face"}>
          <p className="face-name">{card.card_name}</p>
          <p className="face-meta">
            <span>
              {orientationName(card.orientation)} / {orientationNameEn(card.orientation)}
            </span>
          </p>
        </div>
      ) : (
        <p className="waiting">
          尚未翻開<span className="en">Face down</span>
        </p>
      )}
    </article>
  );
}

function InterpretationPanel({
  interpretation,
  busy,
  onInterpret,
}: {
  interpretation: Interpretation | null;
  busy: boolean;
  onInterpret: () => void;
}) {
  if (!interpretation) {
    return (
      <div className="interpret-prompt">
        <p>
          <Copy
            zh="牌陣已完整。解讀只會閱讀已翻開的牌，不會改動牌序或正逆位。"
            en="The spread is complete. An interpretation only reads the revealed cards. It cannot change their order or orientation."
          />
        </p>
        <button className="primary" type="button" disabled={busy} onClick={onInterpret}>
          {busy ? (
            <Copy zh="正在產生…" en="Writing…" />
          ) : (
            <Copy zh="產生示範解讀" en="Create the demonstration reading" />
          )}
        </button>
      </div>
    );
  }

  const structured = interpretation.structured_result;
  const demonstration =
    interpretation.provider === "mock" ||
    interpretation.interpretation_text.includes("DEMONSTRATION ONLY");

  return (
    <article className="interpretation">
      {demonstration ? (
        <p className="banner">
          <Copy
            zh="這是示範解讀，用來確認流程。它不是語言模型寫的占卜。"
            en="This is a demonstration reading used to check the flow. It was not written by a language model."
          />
        </p>
      ) : null}
      <h3>
        整體<span className="en">Overall</span>
      </h3>
      <p>{structured.overall}</p>
      <h3>
        指引<span className="en">Guidance</span>
      </h3>
      <p>{structured.guidance}</p>
      <h3>
        牌與牌的關係<span className="en">How the cards relate</span>
      </h3>
      <p>{structured.relationships}</p>
      <div className="card-readings">
        {structured.card_interpretations.map((card) => (
          <section key={card.position_index}>
            <h4>
              {positionName(card.position_name)}
              {positionName(card.position_name) !== card.position_name
                ? ` / ${card.position_name}`
                : ""}{" "}
              · {card.card_name} · {orientationName(card.orientation)} /{" "}
              {orientationNameEn(card.orientation)}
            </h4>
            <p>{card.interpretation}</p>
          </section>
        ))}
      </div>
      <p className="disclaimer">{structured.disclaimer}</p>
    </article>
  );
}
