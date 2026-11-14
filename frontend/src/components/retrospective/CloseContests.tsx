import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../api/client";
import { partyTagStyle } from "./partyColors";

interface Contest {
  ac_name: string;
  pc_name: string;
  year: number;
  winner_name: string;
  winner_party: string;
  runner_up_name: string | null;
  runner_up_party: string | null;
  margin: number | null;
  margin_percentage: number;
}

function marginClass(pct: number): string {
  if (pct < 1) return "margin-very-close";
  if (pct < 3) return "margin-close";
  return "margin-comfortable";
}

function marginLabel(pct: number): string {
  if (pct < 1) return "Very close";
  if (pct < 3) return "Close";
  return "Comfortable";
}

function marginBarColor(pct: number): string {
  if (pct < 1) return "var(--status-critical)";
  if (pct < 3) return "var(--status-warning)";
  return "var(--status-good)";
}

const YEARS = [2009, 2014, 2019, 2024];
const LATEST_YEAR = String(YEARS[YEARS.length - 1]);
const SLIDER_MAX = 30;
const CHART_ROWS = 15;

export default function CloseContests({ pcName, party }: { pcName: string; party?: string | null }) {
  const [maxMargin, setMaxMargin] = useState(5);
  const [search, setSearch] = useState("");
  const [year, setYear] = useState(LATEST_YEAR);
  const [all, setAll] = useState<Contest[]>([]);

  // Every race for the chosen year comes back once; the slider then narrows
  // it in the browser, so dragging it never waits on the server and the
  // closest race is known even when nothing falls under the slider value.
  useEffect(() => {
    let current = true;
    const params: Record<string, string> = { max_margin_pct: "100" };
    if (pcName) params.pc_name = pcName;
    if (year) params.year = year;
    if (search) params.search = search;
    if (party) params.party = party;
    api.get("/retrospective/close-contests", { params }).then((res) => current && setAll(res.data));
    return () => {
      current = false;
    };
  }, [pcName, year, search, party]);

  const rows = useMemo(() => all.filter((r) => r.margin_percentage <= maxMargin), [all, maxMargin]);
  const closest = all[0];
  const where = pcName ? pcName : "North Andhra";
  const when = year ? year : "all four elections";

  let summary: string;
  if (all.length === 0) {
    summary = "No races match these filters.";
  } else if (rows.length === 0) {
    summary = `No race in ${where} was decided by less than ${maxMargin}% in ${when}. The closest was ${closest.ac_name}${year ? "" : ` in ${closest.year}`}, won by ${closest.margin_percentage.toFixed(1)}%. Slide right to include more races.`;
  } else {
    const word = rows.length === 1 ? "race was" : "races were";
    summary = `${rows.length} ${word} decided by less than ${maxMargin}% in ${where}, ${when} (out of ${all.length} races). The closest: ${rows[0].ac_name}${year ? "" : ` (${rows[0].year})`}, won by ${rows[0].margin_percentage.toFixed(1)}%.`;
  }

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3>
        Close contests{pcName ? `: ${pcName}` : ""}
        {party ? `, ${party} wins only` : ""}
      </h3>
      <p className="chart-caption">Races where the winner's lead over the runner-up was small. A small lead means a small swing could have changed the result.</p>

      <div className="filter-row" style={{ alignItems: "flex-end", marginBottom: 8 }}>
        <div className="margin-control">
          <label htmlFor="margin-slider">
            Show races decided by less than <output htmlFor="margin-slider">{maxMargin}%</output>
          </label>
          <input
            id="margin-slider"
            type="range"
            min={0.5}
            max={SLIDER_MAX}
            step={0.5}
            value={maxMargin}
            onChange={(e) => setMaxMargin(Number(e.target.value))}
          />
          <div className="margin-scale" aria-hidden="true">
            <span>0.5%</span>
            <span>{SLIDER_MAX / 2}%</span>
            <span>{SLIDER_MAX}%</span>
          </div>
        </div>
        <select value={year} onChange={(e) => setYear(e.target.value)} aria-label="Election year">
          <option value="">All years</option>
          {YEARS.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <input type="text" placeholder="Search a constituency" aria-label="Search a constituency" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <p className="close-summary" aria-live="polite">
        {summary}
      </p>

      {rows.length > 0 && (
        <>
          <ResponsiveContainer width="100%" height={Math.max(160, Math.min(rows.length, CHART_ROWS) * 32)}>
            <BarChart data={rows.slice(0, CHART_ROWS)} layout="vertical" margin={{ left: 12, right: 48 }}>
              <XAxis type="number" unit="%" stroke="var(--text-secondary)" fontSize={13} />
              <YAxis type="category" dataKey="ac_name" stroke="var(--text-secondary)" fontSize={13} width={150} />
              <Tooltip
                contentStyle={{
                  background: "var(--surface-1)",
                  border: "1px solid var(--border)",
                  borderRadius: 10,
                  boxShadow: "var(--shadow-pop)",
                  padding: "8px 12px",
                  fontSize: 14,
                  fontFamily: "var(--font-ui)",
                }}
                labelStyle={{ color: "var(--text-primary)", fontWeight: 700 }}
                formatter={(value: number, _n, p: { payload?: Contest }) => [`${value.toFixed(2)}% (${p.payload?.year ?? ""})`, "Winning lead"]}
              />
              <Bar dataKey="margin_percentage" radius={[0, 4, 4, 0]} maxBarSize={20}>
                {rows.slice(0, CHART_ROWS).map((r, i) => (
                  <Cell key={i} fill={marginBarColor(r.margin_percentage)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {rows.length > CHART_ROWS && (
            <p className="chart-caption" style={{ margin: "4px 0 14px" }}>
              The chart shows the closest {CHART_ROWS} of {rows.length} races. The table below lists all of them.
            </p>
          )}

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Constituency</th>
                  <th>Parliamentary seat</th>
                  <th>Year</th>
                  <th>Winner</th>
                  <th>Runner-up</th>
                  <th className="num">Winning lead</th>
                  <th>How close</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={`${r.ac_name}-${r.year}`}>
                    <td style={{ fontWeight: 700 }}>{r.ac_name}</td>
                    <td>{r.pc_name}</td>
                    <td>{r.year}</td>
                    <td>
                      {r.winner_name}{" "}
                      <span className="party-tag" style={partyTagStyle(r.winner_party)}>
                        {r.winner_party}
                      </span>
                    </td>
                    <td>
                      {r.runner_up_name ? (
                        <>
                          {r.runner_up_name}{" "}
                          <span className="party-tag" style={partyTagStyle(r.runner_up_party)}>
                            {r.runner_up_party}
                          </span>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="num">
                      {r.margin_percentage.toFixed(2)}%{r.margin != null && ` (${r.margin.toLocaleString()} votes)`}
                    </td>
                    <td>
                      <span className={`margin-badge ${marginClass(r.margin_percentage)}`}>{marginLabel(r.margin_percentage)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
