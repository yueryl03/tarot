import type {
  DrawRequest,
  Interpretation,
  ReadingCreated,
  ReadingState,
  Spread,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "";

export class ApiError extends Error {
  status: number;
  code: string | null;

  constructor(message: string, status: number, code: string | null) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const CODE_MESSAGE: Record<string, string> = {
  unauthorized: "這次占卜的通行憑證無效。 The reading token is invalid.",
  reading_not_found: "找不到這次占卜。 This reading could not be found.",
  interpretation_not_found: "還沒有解讀。 No interpretation has been stored yet.",
  reading_already_completed: "這次占卜已經抽完。 This reading is already complete.",
  slot_already_revealed: "其中一張牌已經翻開。 One of those cards has already been turned.",
  draw_exceeds_spread: "超過這個牌陣還能抽的張數。 That draw is larger than the spread allows.",
  duplicate_slots: "同一張牌背不能選兩次。 The same card back was selected twice.",
  invalid_slot: "選到了不存在的牌背。 That card back does not exist.",
  reading_not_complete: "牌陣還沒抽完，還不能解讀。 The spread is not complete yet.",
  validation_error: "送出的內容不符合格式。 The request was not valid.",
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return CODE_MESSAGE[error.code ?? ""] ?? error.message;
  }
  if (error instanceof TypeError) {
    return "連不到後端。請先在 backend 目錄啟動 API。 The API is not reachable. Start it from the backend directory.";
  }
  return "發生未預期的錯誤。 Something unexpected went wrong.";
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    let message = response.statusText;
    let code: string | null = null;
    try {
      const body = (await response.json()) as {
        error?: { code?: string; message?: string };
      };
      message = body.error?.message ?? message;
      code = body.error?.code ?? null;
    } catch {
      message = response.statusText;
    }
    throw new ApiError(message, response.status, code);
  }
  return (await response.json()) as T;
}

function authHeaders(token: string, idempotencyKey?: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
  };
}

export function listSpreads(): Promise<{ spreads: Spread[] }> {
  return request("/api/v1/spreads");
}

export function createReading(body: {
  question: string;
  spread_slug: string;
  reversals_enabled: boolean;
}): Promise<ReadingCreated> {
  return request("/api/v1/readings", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getReading(readingId: string, token: string): Promise<ReadingState> {
  return request(`/api/v1/readings/${readingId}`, {
    headers: authHeaders(token),
  });
}

export function drawCards(
  readingId: string,
  token: string,
  body: DrawRequest,
  idempotencyKey: string,
): Promise<unknown> {
  return request(`/api/v1/readings/${readingId}/draw`, {
    method: "POST",
    headers: authHeaders(token, idempotencyKey),
    body: JSON.stringify(body),
  });
}

export function interpretReading(
  readingId: string,
  token: string,
  idempotencyKey: string,
): Promise<Interpretation> {
  return request(`/api/v1/readings/${readingId}/interpret`, {
    method: "POST",
    headers: authHeaders(token, idempotencyKey),
  });
}

export function getInterpretation(
  readingId: string,
  token: string,
): Promise<Interpretation> {
  return request(`/api/v1/readings/${readingId}/interpretation`, {
    headers: authHeaders(token),
  });
}
