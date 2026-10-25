export function Copy({ zh, en }: { zh: string; en: string }) {
  return (
    <span className="copy">
      <span className="zh">{zh}</span>
      <span className="en">{en}</span>
    </span>
  );
}
