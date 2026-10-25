const SPREAD_NAMES: Record<string, string> = {
  "single-card": "單張牌",
  "past-present-future": "三張牌",
  "five-card": "五張牌",
  "celtic-cross": "凱爾特十字",
};

const POSITION_NAMES: Record<string, string> = {
  "Main guidance": "主要指引",
  Past: "過去",
  Present: "現在",
  Future: "未來",
  "Current situation": "當下處境",
  Challenge: "挑戰",
  "Hidden influence": "隱藏影響",
  Advice: "建議",
  "Potential outcome": "可能結果",
  Foundation: "基礎",
  "Recent past": "近況",
  Crown: "冠冕",
  "Near future": "近期",
  Self: "自己",
  Environment: "環境",
  "Hopes and fears": "期望與恐懼",
  Outcome: "結果",
};

const SUIT_NAMES: Record<string, string> = {
  wands: "權杖",
  cups: "聖杯",
  swords: "寶劍",
  pentacles: "錢幣",
};

export function spreadName(spread: { slug: string; name: string }): string {
  return SPREAD_NAMES[spread.slug] ?? spread.name;
}

export function positionName(name: string): string {
  return POSITION_NAMES[name] ?? name;
}

export function suitName(suit: string | null): string | null {
  if (suit === null) {
    return null;
  }
  return SUIT_NAMES[suit] ?? suit;
}

export function orientationName(orientation: string): string {
  return orientation === "reversed" ? "逆位" : "正位";
}

export function orientationNameEn(orientation: string): string {
  return orientation === "reversed" ? "Reversed" : "Upright";
}

export function arcanaName(type: string): string {
  return type === "major" ? "大阿爾克那" : "小阿爾克那";
}

export function arcanaNameEn(type: string): string {
  return type === "major" ? "Major Arcana" : "Minor Arcana";
}

export function suitNameEn(suit: string | null): string | null {
  if (suit === null) {
    return null;
  }
  return suit.charAt(0).toUpperCase() + suit.slice(1);
}

export function statusName(status: string): string {
  if (status === "completed") {
    return "已完成";
  }
  if (status === "in_progress") {
    return "進行中";
  }
  return "尚未抽牌";
}

export function statusNameEn(status: string): string {
  if (status === "completed") {
    return "Complete";
  }
  if (status === "in_progress") {
    return "In progress";
  }
  return "No cards drawn";
}
