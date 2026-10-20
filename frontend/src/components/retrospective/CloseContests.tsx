import { useEffect, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../api/client";
import { partyColor } from "./partyColors";

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

const MARGIN_OPTIONS = [
  { value: "1", label: "Very close (< 1%)" },
  { value: "3", label: "Close (< 3%)" },
  { value: "5", label: "< 5%" },
  { value: "100", label: "All races" },
];

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

export default function CloseContests({ pcName, party }: { pcName: string; party?: string | null }) {
  const [maxMarginPct, setMaxMarginPct] = useState("5");
  const [search, setSearch] = useState("");
  // Defaults to the latest election rather than all 4 years at once -- a
  // table mixing 4 elections' worth of close races reads as one undated
  // list; one year at a time is readable, with "All years" still a click
  // away for whoever wants the full history.
  const [year, setYear] = useState(LATEST_YEAR);
  const [rows, setRows] = useState<Contest[]>([]);

  useEffect(() => {
    const params: Record<string, string> = { max_margin_pct: maxMarginPct };
    if (pcName) params.pc_name = pcName;
    if (year) params.year = year;
    if (search) params.search = search;
    if (party) params.party = party;
    api.get("/retrospective/close-contests", { params }).then((res) => setRows(res.data));
  }, [pcName, maxMarginPct, year, search, party]);

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3>
        Close contest analysis {pcName ? `— ${pcName}` : "(all 5 PCs)"}
        {year ? `, ${year}` : ", all years"}
        {party ? ` · ${party} wins` : ""}
      </h3>
      <div className="filter-row" style={{ marginBottom: 14 }}>
        <select value={maxMarginPct} onChange={(e) => setMaxMarginPct(e.target.value)}>
          {MARGIN_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select value={year} onChange={(e) => setYear(e.target.value)}>
          <option value="">All years</option>
          {YEARS.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <input type="text" placeholder="Search constituency…" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {rows.length === 0 ? (
        <div className="empty-state">No races in this margin range</div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={Math.max(160, Math.min(rows.length, 20) * 28)}>
            <BarChart data={rows.slice(0, 20)} layout="vertical" margin={{ left: 12, right: 44 }}>
              <XAxis type="number" unit="%" stroke="var(--text-muted)" fontSize={12} />
              <YAxis type="category" dataKey="ac_name" stroke="var(--text-muted)" fontSize={12} width={150} />
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
                formatter={(value: number, _n, p: { payload?: Contest }) => [`${value.toFixed(2)}% (${p.payload?.year ?? ""})`, "Margin"]}
              />
              <Bar dataKey="margin_percentage" radius={[0, 4, 4, 0]} maxBarSize={18}>
                {rows.slice(0, 20).map((r, i) => (
                  <Cell key={i} fill={marginBarColor(r.margin_percentage)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {rows.length > 20 && (
            <p className="chart-caption" style={{ margin: "4px 0 14px" }}>
              Showing the closest 20 of {rows.length} races in this range — the full list is in the table below.
            </p>
          )}
        </>
      )}

      {rows.length > 0 && (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>AC</th>
                <th>PC</th>
                <th>Year</th>
                <th>Winner</th>
                <th>Runner-up</th>
                <th className="num">Margin</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{r.ac_name}</td>
                  <td>{r.pc_name}</td>
                  <td>{r.year}</td>
                  <td>
                    {r.winner_name} <span className="party-tag" style={{ background: partyColor(r.winner_party) }}>{r.winner_party}</span>
                  </td>
                  <td>
                    {r.runner_up_name ? (
                      <>
                        {r.runner_up_name}{" "}
                        <span className="party-tag" style={{ background: partyColor(r.runner_up_party) }}>
                          {r.runner_up_party}
                        </span>
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="num">
                    {r.margin_percentage.toFixed(2)}%{r.margin != null && ` (${r.margin.toLocaleString()})`}
                  </td>
                  <td>
                    <span className={`margin-badge ${marginClass(r.margin_percentage)}`}>{marginLabel(r.margin_percentage)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
