import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import BarChartCard from "../components/charts/BarChartCard";
import DonutChartCard from "../components/charts/DonutChartCard";
import { useGlobalFilters } from "../filters";

const CATEGORIES = ["Neutral Influencer", "Volunteer Army"];

interface Respondent {
  id: number;
  pc_name: string | null;
  ac_name: string | null;
  category: string | null;
  occupation: string | null;
  has_phone: boolean;
  contact_name?: string;
  contact_phone_1?: string;
  contact_phone_2?: string;
}

function tally(values: (string | null | undefined)[], limit: number) {
  const counts = new Map<string, number>();
  values.forEach((v) => {
    const name = v || "Not recorded";
    counts.set(name, (counts.get(name) ?? 0) + 1);
  });
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

function plural(n: number, one: string, many = `${one}s`) {
  return `${n} ${n === 1 ? one : many}`;
}

export default function Influencers() {
  const { role } = useAuth();
  const { pcName, acName } = useGlobalFilters();
  const [category, setCategory] = useState("");
  const [summary, setSummary] = useState<{ category: string; count: number }[]>([]);
  const [allRows, setRows] = useState<Respondent[]>([]);
  const [phoneFilter, setPhoneFilter] = useState<"" | "yes" | "no">("");

  const isAdmin = role === "admin";

  useEffect(() => {
    let current = true;
    const params: Record<string, string> = {};
    if (pcName) params.pc_name = pcName;
    if (acName) params.ac_name = acName;
    api.get("/influencers/summary", { params }).then((res) => current && setSummary(res.data));
    return () => {
      current = false;
    };
  }, [pcName, acName]);

  useEffect(() => {
    let current = true;
    const params: Record<string, string> = {};
    if (pcName) params.pc_name = pcName;
    if (acName) params.ac_name = acName;
    if (category) params.category = category;
    api.get("/influencers/list", { params }).then((res) => current && setRows(res.data));
    return () => {
      current = false;
    };
  }, [pcName, acName, category]);

  const rows = useMemo(() => (phoneFilter ? allRows.filter((r) => r.has_phone === (phoneFilter === "yes")) : allRows), [allRows, phoneFilter]);
  const missing = allRows.filter((r) => !r.has_phone);
  const missingByPlace = tally(missing.map((r) => (pcName ? r.ac_name : r.pc_name)), 3);

  function exportCsv() {
    const params = new URLSearchParams();
    if (pcName) params.set("pc_name", pcName);
    if (acName) params.set("ac_name", acName);
    if (category) params.set("category", category);
    if (phoneFilter) params.set("has_phone", phoneFilter);
    const token = localStorage.getItem("access_token");
    fetch(`/api/influencers/export.csv?${params.toString()}`, { headers: token ? { Authorization: `Bearer ${token}` } : undefined })
      .then((res) => res.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = phoneFilter === "yes" ? "influencers_with_phone.csv" : phoneFilter === "no" ? "influencers_missing_phone.csv" : "influencers_and_volunteers.csv";
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  const occupationCounts = useMemo(() => tally(rows.map((r) => r.occupation), 12), [rows]);
  const placeCounts = useMemo(() => tally(rows.map((r) => (acName ? r.occupation : pcName ? r.ac_name : r.pc_name)), 10), [rows, pcName, acName]);

  const categoryCounts = summary.filter((s) => CATEGORIES.includes(s.category));
  const total = categoryCounts.reduce((sum, s) => sum + s.count, 0);
  const neutral = categoryCounts.find((s) => s.category === "Neutral Influencer")?.count ?? 0;
  const volunteers = categoryCounts.find((s) => s.category === "Volunteer Army")?.count ?? 0;
  const place = acName ? acName : pcName ? `${pcName} parliamentary constituency` : "North Andhra";

  const topPlace = placeCounts[0];
  const topJob = occupationCounts[0];
  const placeLabel = acName ? "occupation" : pcName ? "assembly constituency" : "parliamentary constituency";

  const insights: string[] = [];
  if (total > 0 && !acName && topPlace) {
    insights.push(`${topPlace.name} has the most people identified (${topPlace.count} of ${rows.length} listed) among ${placeLabel.replace("constituency", "constituencies")}.`);
  }
  if (topJob && rows.length > 0) {
    insights.push(`${topJob.name} is the most common occupation: ${plural(topJob.count, "person", "people")}, ${Math.round((topJob.count / rows.length) * 100)}% of the list.`);
  }

  return (
    <>
      <h2 className="page-lead">
        {total > 0
          ? `${plural(total, "person", "people")} identified as local influencers or volunteers in ${place}`
          : `No influencers or volunteers recorded yet for ${place}`}
      </h2>
      {total > 0 && (
        <p className="page-lead-sub">
          {neutral} {neutral === 1 ? "is a neutral influencer" : "are neutral influencers"} and {volunteers} {volunteers === 1 ? "is a volunteer" : "are volunteers"}. These come from the survey responses loaded so
          far; change the Scope filter at the top to look at one constituency.
        </p>
      )}

      {!isAdmin && (
        <div className="card" style={{ marginBottom: 20, borderColor: "var(--status-critical)" }}>
          <span className="pii-pill">Names and numbers hidden</span>{" "}
          <span style={{ fontSize: 15, color: "var(--text-secondary)" }}>
            Names and phone numbers are visible to Admin accounts only. You are seeing counts and occupations.
          </span>
        </div>
      )}

      {missing.length > 0 && (
        <div className="callout-warning" role="status">
          <div>
            <strong>
              {missing.length} of {allRows.length} people have no phone number, so the team cannot call them.
            </strong>
            <p>
              Only {allRows.length - missing.length} can be reached by phone today.
              {missingByPlace.length > 0 && ` Most of the gaps are in ${missingByPlace.map((m) => `${m.name} (${m.count})`).join(", ")}.`}
            </p>
          </div>
          <div className="callout-actions">
            <button type="button" className="primary" aria-pressed={phoneFilter === "yes"} onClick={() => setPhoneFilter(phoneFilter === "yes" ? "" : "yes")}>
              {phoneFilter === "yes" ? "Show everyone" : "Show only people with a number"}
            </button>
            <button type="button" className="secondary-action" aria-pressed={phoneFilter === "no"} onClick={() => setPhoneFilter(phoneFilter === "no" ? "" : "no")}>
              {phoneFilter === "no" ? "Show everyone" : "Show who is missing a number"}
            </button>
          </div>
        </div>
      )}

      {insights.length > 0 && (
        <ul className="takeaway-list">
          {insights.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      )}

      <div className="filter-row">
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Show which group">
          <option value="">Both groups</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select value={phoneFilter} onChange={(e) => setPhoneFilter(e.target.value as "" | "yes" | "no")} aria-label="Filter by phone number">
          <option value="">With or without a phone number</option>
          <option value="yes">Only people with a phone number</option>
          <option value="no">Only people missing a phone number</option>
        </select>
        {isAdmin && (
          <button type="button" className="primary" style={{ marginLeft: "auto" }} onClick={exportCsv}>
            Download this list (CSV)
          </button>
        )}
      </div>

      <div className="grid cols-2" style={{ marginBottom: 20 }}>
        <DonutChartCard
          title="Neutral influencers and volunteers"
          data={categoryCounts.map((s) => ({ name: s.category, count: s.count, pct: total ? Math.round((s.count / total) * 1000) / 10 : 0 }))}
          colorOffset={2}
        />
        <BarChartCard title={`Most common occupations`} data={occupationCounts} colorIndex={3} />
      </div>

      {!acName && <BarChartCard title={`People identified, by ${placeLabel}`} data={placeCounts} colorIndex={1} />}

      <div className="card" style={{ marginTop: 20 }}>
        <h3>
          People listed ({rows.length}
          {phoneFilter === "yes" ? ", all with a phone number" : phoneFilter === "no" ? ", all missing a phone number" : ""})
        </h3>
        {rows.length === 0 ? (
          <div className="empty-state">Nobody matches these filters. Try a wider Scope, Both groups, or With or without a phone number.</div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Parliamentary constituency</th>
                  <th>Assembly constituency</th>
                  <th>Group</th>
                  <th>Occupation</th>
                  {isAdmin && <th>Name</th>}
                  {isAdmin && <th>Phone 1</th>}
                  {isAdmin && <th>Phone 2</th>}
                  {!isAdmin && <th>Phone number</th>}
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
                    {isAdmin && (
                      <td className="tabular-nums">{r.has_phone ? r.contact_phone_1 || "—" : <span className="margin-badge margin-very-close">No phone number</span>}</td>
                    )}
                    {isAdmin && <td className="tabular-nums">{r.contact_phone_2 || "—"}</td>}
                    {!isAdmin && <td>{r.has_phone ? "On file" : <span className="margin-badge margin-very-close">No phone number</span>}</td>}
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
