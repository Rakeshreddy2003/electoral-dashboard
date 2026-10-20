import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { seriesColor } from "./palette";

interface Datum {
  name: string;
  code?: string | null;
  count: number;
}

const CHARS_PER_LINE = 22;
const LINE_HEIGHT = 13;
const MAX_LINES = 2;

// Wrap at word boundaries, capped at MAX_LINES -- an earlier version wrapped
// onto as many lines as a label needed with no cap, so the one longest
// label in the dataset (a 4-line risk-incident sentence) forced every row
// in the chart to that same tall row height, even rows whose own label was
// one line. Capping to 2 lines (with an ellipsis on the rare label that
// still overflows) keeps row height proportional to what most labels
// actually need; the full text is always available in the tooltip, which
// shows the untruncated category name regardless of what the axis tick
// displays.
function wrapLabel(label: string): string[] {
  const words = label.split(" ");
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length > CHARS_PER_LINE && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
    if (lines.length === MAX_LINES) break;
  }
  if (lines.length < MAX_LINES && current) lines.push(current);

  if (lines.length === MAX_LINES) {
    const consumed = lines.join(" ").length;
    if (consumed < label.length) {
      const last = lines[MAX_LINES - 1];
      lines[MAX_LINES - 1] = last.length > 2 ? `${last.slice(0, -1)}…` : `${last}…`;
    }
  }
  return lines;
}

function maxLineCount(data: Datum[]): number {
  return data.reduce((max, d) => Math.max(max, wrapLabel(d.name).length), 1);
}

function AxisTick({ x, y, payload }: { x: number; y: number; payload: { value: string } }) {
  const lines = wrapLabel(payload.value);
  const startDy = -((lines.length - 1) * LINE_HEIGHT) / 2 + 4;
  return (
    <text x={x} y={y} textAnchor="end" fontSize={12} fill="var(--text-muted)">
      {lines.map((line, i) => (
        <tspan key={i} x={x} dy={i === 0 ? startDy : LINE_HEIGHT}>
          {line}
        </tspan>
      ))}
    </text>
  );
}

interface BarChartCardProps {
  title: string;
  data: Datum[];
  colorIndex?: number;
  valueLabel?: string;
  valueFormatter?: (value: number) => string;
  /** Set to make bars clickable -- used for cross-filtering (see Responses.tsx). */
  onBarClick?: (datum: Datum) => void;
  /** The currently active filter value for this chart's field, if any -- highlights the matching bar. */
  activeCode?: string | null;
}

export default function BarChartCard({
  title,
  data,
  colorIndex = 0,
  valueLabel = "Count",
  valueFormatter,
  onBarClick,
  activeCode,
}: BarChartCardProps) {
  const lineCount = maxLineCount(data);
  const rowHeight = 30 + (lineCount - 1) * LINE_HEIGHT;
  const height = Math.max(220, data.length * rowHeight);
  const format = valueFormatter ?? ((v: number) => v.toLocaleString());
  const baseColor = seriesColor(colorIndex);
  const Y_AXIS_WIDTH = 190; // labels wrap within this instead of extending it, see wrapLabel()

  return (
    <div className="card">
      <h3 className="card-title">{title}</h3>
      {data.length === 0 ? (
        <div className="empty-state">No data yet</div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} layout="vertical" margin={{ left: 12, right: 56 }}>
            <CartesianGrid stroke="var(--gridline)" horizontal={false} />
            <XAxis type="number" stroke="var(--text-muted)" fontSize={12} allowDecimals={false} />
            <YAxis type="category" dataKey="name" stroke="var(--text-muted)" fontSize={12} width={Y_AXIS_WIDTH} tick={AxisTick as never} />
            <Tooltip
              cursor={{ fill: "var(--surface-sunken)" }}
              contentStyle={{
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                borderRadius: 10,
                boxShadow: "var(--shadow-pop)",
                padding: "8px 12px",
                fontSize: 13,
                fontFamily: "var(--font-ui)",
              }}
              labelStyle={{ color: "var(--text-primary)", fontWeight: 600, marginBottom: 2 }}
              formatter={(value: number) => [format(value), valueLabel]}
            />
            <Bar
              dataKey="count"
              radius={[0, 4, 4, 0]}
              maxBarSize={22}
              onClick={onBarClick ? (datum: Datum) => onBarClick(datum) : undefined}
              cursor={onBarClick ? "pointer" : "default"}
            >
              {data.map((d, i) => (
                <Cell
                  key={i}
                  fill={baseColor}
                  fillOpacity={activeCode ? (d.code === activeCode ? 1 : 0.3) : 1}
                />
              ))}
              <LabelList dataKey="count" position="right" formatter={format as never} style={{ fill: "var(--text-secondary)", fontSize: 12 }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
