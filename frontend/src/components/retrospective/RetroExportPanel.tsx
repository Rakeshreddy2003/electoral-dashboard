import { useState } from "react";

const SCOPES = [
  { value: "both", label: "Assembly + Lok Sabha" },
  { value: "ae", label: "Assembly (AE) only" },
  { value: "ge", label: "Lok Sabha (GE) only" },
];

const YEARS = [2009, 2014, 2019, 2024];

// Mirrors the page's own scope rule (ac > pc > all of North Andhra): the
// export always matches whatever the global PC/AC filter is currently
// showing, so there's nothing extra to pick here beyond election type and
// which years to include -- no years checked means "all years", same as
// what the backend does when the years param is omitted.
export default function RetroExportPanel({ pcName, acName }: { pcName: string; acName: string }) {
  const [scope, setScope] = useState("both");
  const [years, setYears] = useState<number[]>([]);
  const [downloading, setDownloading] = useState(false);

  function toggleYear(y: number) {
    setYears((prev) => (prev.includes(y) ? prev.filter((v) => v !== y) : [...prev, y]));
  }

  function download() {
    const params = new URLSearchParams();
    if (pcName) params.set("pc_name", pcName);
    if (acName) params.set("ac_name", acName);
    params.set("scope", scope);
    years.forEach((y) => params.append("years", String(y)));

    const token = localStorage.getItem("access_token");
    setDownloading(true);
    fetch(`/api/retrospective/export.xlsx?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${(acName || pcName || "north_andhra").replace(/\s+/g, "_")}_retrospective.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
      })
      .finally(() => setDownloading(false));
  }

  return (
    <div className="card" style={{ marginBottom: 20, display: "flex", flexWrap: "wrap", alignItems: "center", gap: 14 }}>
      <div style={{ flex: "1 1 240px" }}>
        <h3 style={{ margin: "0 0 4px" }}>Download data</h3>
        <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)" }}>
          {acName
            ? `${acName} (assembly) and its Lok Sabha constituency, as Excel.`
            : pcName
            ? `${pcName} Lok Sabha result and all its assembly segments, as Excel.`
            : "All of North Andhra's assembly and Lok Sabha results, as Excel."}
        </p>
      </div>

      <select value={scope} onChange={(e) => setScope(e.target.value)} aria-label="Election type">
        {SCOPES.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {YEARS.map((y) => (
          <label key={y} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 13, color: "var(--text-secondary)" }}>
            <input type="checkbox" checked={years.includes(y)} onChange={() => toggleYear(y)} />
            {y}
          </label>
        ))}
      </div>

      <button type="button" className="primary" onClick={download} disabled={downloading}>
        {downloading ? "Preparing…" : "Download Excel"}
      </button>
    </div>
  );
}
