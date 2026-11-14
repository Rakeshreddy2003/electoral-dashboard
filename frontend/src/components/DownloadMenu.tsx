import { useEffect, useRef, useState } from "react";
import { useAuth } from "../auth/AuthContext";

const SCOPES = [
  { value: "both", label: "Assembly and Lok Sabha results" },
  { value: "ae", label: "Assembly results only" },
  { value: "ge", label: "Lok Sabha results only" },
];

const YEARS = [2009, 2014, 2019, 2024];

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// Lives in the masthead so field teams can pull data from any page without
// scrolling. It always downloads what the Scope filter above it shows.
export default function DownloadMenu({ pcName, acName }: { pcName: string; acName: string }) {
  const { role } = useAuth();
  const [open, setOpen] = useState(false);
  const [scope, setScope] = useState("both");
  const [years, setYears] = useState<number[]>([]);
  const [busy, setBusy] = useState<"results" | "contacts" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const place = acName ? `${acName} assembly constituency` : pcName ? `${pcName} parliamentary constituency` : "all of North Andhra";
  const token = localStorage.getItem("access_token");
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;

  function toggleYear(y: number) {
    setYears((prev) => (prev.includes(y) ? prev.filter((v) => v !== y) : [...prev, y]));
  }

  async function download(kind: "results" | "contacts") {
    setBusy(kind);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (pcName) params.set("pc_name", pcName);
      if (acName) params.set("ac_name", acName);
      let url: string;
      let filename: string;
      if (kind === "results") {
        params.set("scope", scope);
        years.forEach((y) => params.append("years", String(y)));
        url = `/api/retrospective/export.xlsx?${params.toString()}`;
        filename = `${(acName || pcName || "north_andhra").replace(/\s+/g, "_")}_election_results.xlsx`;
      } else {
        url = `/api/influencers/export.csv?${params.toString()}`;
        filename = "influencers_and_volunteers.csv";
      }
      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error(`The server answered ${res.status}`);
      saveBlob(await res.blob(), filename);
    } catch (e) {
      setError(`Download failed. ${(e as Error).message}. Try again, or ask an admin to check the server.`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="download-wrap" ref={wrapRef}>
      <button type="button" className="primary download-trigger" aria-expanded={open} aria-haspopup="dialog" onClick={() => setOpen((o) => !o)}>
        Download data
      </button>
      {open && (
        <div className="download-panel" role="dialog" aria-label="Download data">
          <h4>Download data</h4>
          <p>You will get {place}, matching the Scope filter above.</p>

          <label className="field-label" htmlFor="dl-scope">
            Election results
          </label>
          <select id="dl-scope" value={scope} onChange={(e) => setScope(e.target.value)}>
            {SCOPES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>

          <span className="field-label">Years (leave empty for all four)</span>
          <div className="year-chips">
            {YEARS.map((y) => (
              <label key={y}>
                <input type="checkbox" checked={years.includes(y)} onChange={() => toggleYear(y)} />
                {y}
              </label>
            ))}
          </div>

          <button type="button" className="primary" onClick={() => download("results")} disabled={busy !== null}>
            {busy === "results" ? "Preparing the Excel file…" : "Download results (Excel)"}
          </button>

          {role === "admin" && (
            <button type="button" className="secondary-action" onClick={() => download("contacts")} disabled={busy !== null}>
              {busy === "contacts" ? "Preparing the CSV…" : "Download influencer and volunteer contacts (CSV)"}
            </button>
          )}

          <p className="download-soon">
            <strong>Form 20 and polling booth lists</strong> will appear here as booth-wise sheets once that data is loaded, so teams can pull booth names and
            vote counts for the same area.
          </p>

          {error && <p className="error-text">{error}</p>}
        </div>
      )}
    </div>
  );
}
