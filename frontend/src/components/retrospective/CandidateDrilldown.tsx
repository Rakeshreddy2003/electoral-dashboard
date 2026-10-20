import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../../api/client";
import { partyColor } from "./partyColors";

interface Candidate {
  year: number;
  ac_name: string;
  candidate_name: string;
  party: string;
  position: number;
  vote_share_percentage: number;
  margin_percentage: number;
  turnout_percentage: number;
  total_electors: number;
}

export default function CandidateDrilldown({ acName, years }: { acName: string; years: number[] }) {
  const [year, setYear] = useState<number | "">(years[years.length - 1] ?? "");
  const [rows, setRows] = useState<Candidate[]>([]);

  useEffect(() => {
    setYear(years[years.length - 1] ?? "");
  }, [acName, years]);

  useEffect(() => {
    if (!year) return;
    api.get("/retrospective/results", { params: { ac_name: acName, year } }).then((res) => setRows(res.data));
  }, [acName, year]);

  const chartData = rows.map((r) => ({ name: r.candidate_name, voteShare: r.vote_share_percentage, party: r.party }));

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3>Full candidate result — {acName}</h3>
      <div className="filter-row" style={{ marginBottom: 14 }}>
        <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {years.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      {rows.length === 0 ? (
        <div className="empty-state">No data</div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={Math.max(220, rows.length * 32)}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 12, right: 40 }}>
              <CartesianGrid stroke="var(--gridline)" horizontal={false} />
              <XAxis type="number" stroke="var(--text-muted)" fontSize={12} unit="%" />
              <YAxis type="category" dataKey="name" stroke="var(--text-muted)" fontSize={12} width={160} />
              <Tooltip
                contentStyle={{ background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                formatter={(value: number) => `${value.toFixed(1)}%`}
              />
              <Bar dataKey="voteShare" radius={[0, 4, 4, 0]} maxBarSize={22}>
                {chartData.map((c, i) => (
                  <Cell key={i} fill={partyColor(c.party)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="table-scroll" style={{ marginTop: 16 }}>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Candidate</th>
                  <th>Party</th>
                  <th className="num">Vote share %</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i}>
                    <td>{r.position}</td>
                    <td>{r.candidate_name}</td>
                    <td>
                      <span className="party-tag" style={{ background: partyColor(r.party) }}>
                        {r.party}
                      </span>
                    </td>
                    <td className="num">{r.vote_share_percentage?.toFixed(1)}</td>
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
