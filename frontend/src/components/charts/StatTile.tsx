interface StatTileProps {
  label: string;
  value: string | number;
  fill?: boolean;
  /** "brand" for a key metric (colored, draws the eye), "good"/"bad" for a signed finding (turnout up/down), "neutral" for static reference numbers that shouldn't compete for attention. Defaults to "brand". */
  tone?: "brand" | "good" | "bad" | "neutral";
}

// Deliberately NOT a .card -- a boxed, bordered, colored-accent "hero
// metric" tile is the generic-dashboard default, and nesting it inside
// another .card (as the Retrospective "at a glance" panel did) produced a
// literal card-in-a-card. This is plain typography: a colored number and
// a label, sitting directly on whatever surface it's placed in. Color
// alone carries which tone it is -- no border, no background box.
export default function StatTile({ label, value, fill, tone = "brand" }: StatTileProps) {
  return (
    <div className={`stat-tile stat-tile-${tone}`} style={fill ? { flex: 1, justifyContent: "center" } : undefined}>
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}
