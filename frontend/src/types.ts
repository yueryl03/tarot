export type Orientation = "upright" | "reversed";
export type ReadingStatus = "created" | "in_progress" | "completed";

export interface SpreadPosition {
  position_index: number;
  name: string;
  description: string;
}

export interface Spread {
  id: number;
  slug: string;
  name: string;
  description: string;
  card_count: number;
  created_at: string;
  positions: SpreadPosition[];
}

export interface RevealedCard {
  card_id: number;
  card_name: string;
  arcana_type: "major" | "minor";
  suit: "wands" | "cups" | "swords" | "pentacles" | null;
  rank: string;
  canonical_number: number;
  image_key: string | null;
  orientation: Orientation;
  slot_index: number;
  spread_position_index: number;
  spread_position_name: string;
  spread_position_description: string;
  draw_order: number;
  revealed_at: string;
  keywords: string[];
  general_meaning: string;
}

export interface ReadingState {
  reading_id: string;
  question: string;
  status: ReadingStatus;
  reversals_enabled: boolean;
  spread: Spread;
  available_count: number;
  revealed_slot_indices: number[];
  remaining_positions: SpreadPosition[];
  draws: RevealedCard[];
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface ReadingCreated extends ReadingState {
  access_token: string;
  token_type: "bearer";
}

export interface CardInterpretation {
  position_index: number;
  position_name: string;
  card_name: string;
  orientation: string;
  interpretation: string;
}

export interface Interpretation {
  id: string;
  reading_id: string;
  provider: string;
  model_name: string;
  interpretation_text: string;
  structured_result: {
    card_interpretations: CardInterpretation[];
    relationships: string;
    overall: string;
    guidance: string;
    disclaimer: string;
  };
  created_at: string;
}

export type DrawRequest =
  | { mode: "top"; count: number }
  | { mode: "select"; slot_indices: number[] };
