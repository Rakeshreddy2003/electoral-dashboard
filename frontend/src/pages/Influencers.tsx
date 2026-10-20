import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import BarChartCard from "../components/charts/BarChartCard";
import DonutChartCard from "../components/charts/DonutChartCard";
import PageHeader from "../components/PageHeader";
import { useGlobalFilters } from "../filters";

const CATEGORIES = ["Neutral Influencer", "Volunteer Army"];

interface Respondent {
  id: number;
  pc_name: string | null;
  ac_name: string | null;
  category: string | null;
  occupation: string | null;
  contact_name?: string;
  contact_phone_1?: string;
  contact_phone_2?: string;
}

export default function Influencers() {
  const { role } = useAuth();
  const { pcName, acName } = useGlobalFilters();
  const [category, setCategory] = useState("");
  const [summary, setSummary] = useState<{ category: string; count: number }[]>([]);
  const [rows, setRows] = useState<Respondent[]>([]);

  const isAdmin = role === "admin";

  // Occupation breakdown of the currently filtered respondents -- computed
  // client-side from the already-fetched, already-filtered /list rows
  // rather than a new endpoint, since every row already carries occupation.
  const occupationCounts = useMemo(() => {
    const counts = new Map<string, number>();
    rows.forEach((r) => {
      const name = r.occupation || "Unknown";
      counts.set(name, (counts.get(name) ?? 0) + 1);
    });
    return [...counts.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 12);
  }, [rows]);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (pcName) params.pc_name = pcName;
    if (acName) params.ac_name = acName;
    api.get("/influencers/summary", { params }).then((res) => setSummary(res.data));
  }, [pcName, acName]);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (pcName) params.pc_name = pcName;
    if (acName) params.ac_name = acName;
    if (category) params.category = category;
    api.get("/influencers/list", { params }).then((res) => setRows(res.data));
  }, [pcName, acName, category]);

  function exportCsv() {
    const params = new URLSearchParams();
    if (pcName) params.set("pc_name", pcName);
    if (acName) params.set("ac_name", acName);
    if (category) params.set("category", category);
    const token = localStorage.getItem("access_token");
    fetch(`/api/influencers/export.csv?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "influencers_volunteers.csv";
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  return (
    <>
      <PageHeader
        title="Influencers / Volunteers"
        accent="Volunteers"
        subtitle="Field-identified neutral influencers and volunteer army contacts, by constituency."
      />

      {!isAdmin && (
        <div className="card" style={{ marginBottom: 20, borderColor: "var(--status-critical)" }}>
          <span className="pii-pill">PII restricted</span>{" "}
          <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
            Names and phone numbers for Neutral Influencers / Volunteer Army are visible to Admin accounts only. You're seeing
            aggregate counts and non-PII fields.
          </span>
        </div>
      )}

      <div className="filter-row">
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">Both categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        {isAdmin && (
          <button className="primary" onClick={exportCsv} style={{ marginLeft: "auto" }}>
            Export CSV (with contact details)
          </button>
        )}
      </div>

      {/* The donut's legend already carries both the count and the share
          ("76 · 80%"), so a separate pair of StatTiles repeating the same
          two numbers next to it would just be the same fact twice --
          professions sits beside it instead, since that's new information. */}
      <div className="grid cols-2" style={{ marginBottom: 20 }}>
        <DonutChartCard
          title="Count by category"
          data={(() => {
            const counts = summary.filter((s) => CATEGORIES.includes(s.category));
            const total = counts.reduce((sum, s) => sum + s.count, 0);
            return counts.map((s) => ({ name: s.category, count: s.count, pct: total ? Math.round((s.count / total) * 1000) / 10 : 0 }));
          })()}
          colorOffset={2}
        />
        <BarChartCard
          title={`Professions — ${category || "neutral influencers & volunteer army"}`}
          data={occupationCounts}
          colorIndex={3}
        />
      </div>

      <div className="card">
        <h3>Respondents ({rows.length})</h3>
        {rows.length === 0 ? (
          <div className="empty-state">No data yet</div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>PC</th>
                  <th>AC</th>
                  <th>Category</th>
                  <th>Occupation</th>
                  {isAdmin && <th>Name</th>}
                  {isAdmin && <th>Phone 1</th>}
                  {isAdmin && <th>Phone 2</th>}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.pc_name || "—"}</td>
                    <td>{r.ac_name || "—"}</td>
                    <td>{r.category || "—"}</td>
                    <td>{r.occupation || "—"}</td>
                    {isAdmin && <td>{r.contact_name || "—"}</td>}
                    {isAdmin && <td className="tabular-nums">{r.contact_phone_1 || "—"}</td>}
                    {isAdmin && <td className="tabular-nums">{r.contact_phone_2 || "—"}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
