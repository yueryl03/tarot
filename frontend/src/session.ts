const KEY = "tarot.reading";

export interface StoredReading {
  readingId: string;
  accessToken: string;
}

export function loadSession(): StoredReading | null {
  const raw = localStorage.getItem(KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as StoredReading;
    if (!parsed.readingId || !parsed.accessToken) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveSession(session: StoredReading): void {
  localStorage.setItem(KEY, JSON.stringify(session));
}

export function clearSession(): void {
  localStorage.removeItem(KEY);
}
