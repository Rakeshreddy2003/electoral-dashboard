import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { seriesColor } from "./palette";

interface DonutDatum {
  name: string;
  pct: number;
  code?: string | null;
  /** Raw count, shown beside the percentage in the legend when provided ("76 · 80%") -- a percentage alone doesn't tell you whether a slice is 76 of 95 or 3 of 4. */
  count?: number;
}

interface DonutChartCardProps {
  title: string;
  caption?: string;
  data: DonutDatum[];
  colorOffset?: number;
  /** Overrides the generic categorical palette -- e.g. party colors, where a slice's color is tied to its identity, not its position in the data array. */
  colorFor?: (datum: DonutDatum) => string;
  /** Set to make slices clickable -- used for cross-filtering (see Responses.tsx), same contract as BarChartCard. */
  onSliceClick?: (datum: DonutDatum) => void;
  /** The currently active filter value for this chart's field, if any -- highlights the matching slice. */
  activeCode?: string | null;
}

function luminance(hex: string): number {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0, 2), 16) || 0;
  const g = parseInt(h.slice(2, 4), 16) || 0;
  const b = parseInt(h.slice(4, 6), 16) || 0;
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
}

// Labels sit INSIDE the ring (midway between inner and outer radius), not
// floating outside it -- a previous version positioned them outside at
// outerRadius + a fixed offset, which only stayed inside the SVG canvas
// for one specific combination of chart size/margin/radius. Any of those
// changing (as happened) pushed the label past the canvas edge and
// clipped it. A radius that is, by construction, always less than
// outerRadius can never do that, at any size this component is ever used
// at. Text color is chosen per slice for contrast (white on a dark fill,
// near-black on a light one) instead of one fixed color, which is also
// what makes the label legible against any series/party color.
function renderLabel({ cx, cy, midAngle, innerRadius, outerRadius, pct, fill }: any) {
  if (pct < 10) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) / 2;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  const textColor = luminance(fill) > 0.6 ? "#14151c" : "#ffffff";
  return (
    <text x={x} y={y} fill={textColor} fontSize={12} fontWeight={700} textAnchor="middle" dominantBaseline="central">
      {pct}%
    </text>
  );
}

export default function DonutChartCard({ title, caption, data, colorOffset = 0, colorFor, onSliceClick, activeCode }: DonutChartCardProps) {
  return (
    <div className="card">
      <h3 className="card-title">{title}</h3>
      {caption && <p className="chart-caption">{caption}</p>}
      {data.length === 0 ? (
        <div className="empty-state">No data yet</div>
      ) : (
        // A plain HTML legend, not recharts' own <Legend> -- recharts
        // always anchors Legend to the far edge of whatever width
        // ResponsiveContainer gets, so a card wider than the chart+legend
        // actually need (e.g. only 2-3 items) left a dead gap between
        // them. The chart itself is genuinely responsive now (width:
        // "100%" of its flex-growing wrapper, not a fixed pixel box) --
        // it was fixed at 190x190 before, which read as a small donut
        // lost in a lot of empty card on a wide monitor. flex: 1 1 320px
        // lets it grow to fill whatever space the card has beyond the
        // legend's own natural width, and shrink back down on a narrow
        // card/viewport instead of overflowing it. The inside-ring label
        // position (above) is percentage-based off the resolved pixel
        // radius, so it stays correct at any size this produces.
        <div className="donut-row">
          <div className="donut-chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={data}
                dataKey="pct"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius="55%"
                outerRadius="92%"
                paddingAngle={1}
                label={renderLabel}
                labelLine={false}
                onClick={onSliceClick ? (datum: DonutDatum) => onSliceClick(datum) : undefined}
                cursor={onSliceClick ? "pointer" : "default"}
              >
                {data.map((d, i) => (
                  <Cell
                    key={i}
                    fill={colorFor ? colorFor(d) : seriesColor(i + colorOffset)}
                    stroke="var(--surface-1)"
                    strokeWidth={2}
                    fillOpacity={activeCode ? (d.code === activeCode ? 1 : 0.35) : 1}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--surface-1)",
                  border: "1px solid var(--border)",
                  borderRadius: 10,
                  boxShadow: "var(--shadow-pop)",
                  padding: "8px 12px",
                  fontSize: 13,
                  fontFamily: "var(--font-ui)",
                }}
                labelStyle={{ color: "var(--text-primary)", fontWeight: 600 }}
                formatter={(value: number, name: string) => [`${value}%`, name]}
              />
            </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="donut-legend">
            {data.map((d, i) => (
              <li
                key={i}
                onClick={onSliceClick ? () => onSliceClick(d) : undefined}
                style={{
                  cursor: onSliceClick ? "pointer" : "default",
                  opacity: activeCode ? (d.code === activeCode ? 1 : 0.5) : 1,
                }}
              >
                <span className="dot" style={{ background: colorFor ? colorFor(d) : seriesColor(i + colorOffset) }} />
                <span className="name">{d.name}</span>
                <span className="pct">
                  {d.count != null ? `${d.count.toLocaleString()} · ` : ""}
                  {d.pct}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
