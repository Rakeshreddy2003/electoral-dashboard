import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

interface GroupedBarChartCardProps {
  title: string;
  caption?: string;
  data: Record<string, number | string>[];
  xKey: string;
  seriesKeys: string[];
  colorFor: (key: string) => string;
  /** Set to make a series (e.g. a party) clickable -- clicking any of its bars filters the page by it, same cross-filter contract as BarChartCard/DonutChartCard. */
  onSeriesClick?: (key: string) => void;
  /** The currently active filter value, if any -- dims the other series. */
  activeKey?: string | null;
}

function hideZero(v: number) {
  return v > 0 ? v : "";
}

// Recharts allocates one equal-width slot per series across the *entire*
// shared axis -- a party with 0 seats in a given year still reserves that
// year's slot for it, just empty, so the bars that do have seats can't
// grow to use the freed space. There's no prop for "skip zero slots and
// widen the rest" on a single shared-axis chart; the only way to actually
// reclaim that width is to give each year its own independent axis (and
// therefore its own bar-slot count), the same way the reference TN
// dashboard this was modeled on used a separate bar chart per year rather
// than one combined one.
function YearTooltip({ active, yearLabel, row, seriesKeys, colorFor }: {
  active?: boolean;
  yearLabel: string;
  row: Record<string, number | string>;
  seriesKeys: string[];
  colorFor: (key: string) => string;
}) {
  if (!active) return null;
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        boxShadow: "var(--shadow-pop)",
        padding: "8px 12px",
        fontSize: 14,
        fontFamily: "var(--font-ui)",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4, color: "var(--text-primary)" }}>{yearLabel}</div>
      {seriesKeys.map((key) => {
        const v = Number(row[key]) || 0;
        return (
          <div key={key} style={{ color: colorFor(key) }}>
            {key} : {v} seat{v === 1 ? "" : "s"}
          </div>
        );
      })}
    </div>
  );
}

export default function GroupedBarChartCard({ title, caption, data, xKey, seriesKeys, colorFor, onSeriesClick, activeKey }: GroupedBarChartCardProps) {
  const maxSeats = Math.max(1, ...data.flatMap((row) => seriesKeys.map((k) => Number(row[k]) || 0)));
  const yDomain: [number, number] = [0, Math.ceil(maxSeats / 8) * 8 || 8];

  return (
    <div className="card">
      <h3 className="card-title">{title}</h3>
      {caption && <p className="chart-caption">{caption}</p>}
      {data.length === 0 || seriesKeys.length === 0 ? (
        <div className="empty-state">No data yet</div>
      ) : (
        <>
          {/* A plain HTML legend, same reasoning as DonutChartCard's --
              recharts' own <Legend> expects to live inside one chart's
              context; this card now renders 4 independent charts (one per
              year) sharing a single color key above them, which a real
              chart-bound Legend component isn't built for. */}
          <ul className="donut-legend" style={{ flexDirection: "row", flexWrap: "wrap", justifyContent: "flex-end", marginBottom: 12 }}>
            {seriesKeys.map((key) => (
              <li key={key} style={{ cursor: onSeriesClick ? "pointer" : "default", opacity: activeKey ? (key === activeKey ? 1 : 0.5) : 1 }} onClick={onSeriesClick ? () => onSeriesClick(key) : undefined}>
                <span className="dot" style={{ background: colorFor(key) }} />
                <span className="name">{key}</span>
              </li>
            ))}
          </ul>
          <div style={{ display: "flex", gap: 20 }}>
            {data.map((row, i) => {
              const yearLabel = `${row[xKey]} assembly election`;
              const entries = seriesKeys
                .filter((key) => Number(row[key]) > 0)
                .map((key) => ({ name: key, value: Number(row[key]) }));
              return (
                <div key={String(row[xKey])} style={{ flex: 1, minWidth: 0 }}>
                  <ResponsiveContainer width="100%" height={340}>
                    <BarChart data={entries} margin={{ left: 4, right: 4, top: 8, bottom: 4 }} barCategoryGap="22%">
                      <CartesianGrid stroke="var(--gridline)" vertical={false} strokeDasharray="3 4" />
                      <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={13} tickLine={false} axisLine={{ stroke: "var(--border)" }} interval={0} />
                      <YAxis
                        domain={yDomain}
                        stroke="var(--text-muted)"
                        fontSize={13}
                        allowDecimals={false}
                        width={i === 0 ? 34 : 0}
                        tick={i === 0}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        content={<YearTooltip yearLabel={yearLabel} row={row} seriesKeys={seriesKeys} colorFor={colorFor} />}
                        cursor={{ fill: "var(--surface-sunken)" }}
                      />
                      <Bar
                        dataKey="value"
                        radius={[4, 4, 0, 0]}
                        maxBarSize={60}
                        onClick={onSeriesClick ? (d: { name: string }) => onSeriesClick(d.name) : undefined}
                        cursor={onSeriesClick ? "pointer" : "default"}
                      >
                        {entries.map((e, ei) => (
                          <Cell key={ei} fill={colorFor(e.name)} fillOpacity={activeKey ? (e.name === activeKey ? 1 : 0.3) : 1} />
                        ))}
                        <LabelList dataKey="value" position="top" formatter={hideZero as never} style={{ fontSize: 14, fontWeight: 700, fill: "var(--text-secondary)" }} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div style={{ textAlign: "center", fontSize: 14, fontWeight: 600, color: "var(--text-muted)", marginTop: 4 }}>{row[xKey]}</div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
