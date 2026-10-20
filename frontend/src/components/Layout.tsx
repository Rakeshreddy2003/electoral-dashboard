import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import { Ac } from "../filters";

const PAGES = [
  { to: "/retrospective", label: "Retrospective Data" },
  { to: "/responses", label: "Form Responses" },
  { to: "/influencers", label: "Influencers / Volunteers" },
];

const PC_NAMES = ["Araku", "Srikakulam", "Vizianagaram", "Visakhapatnam", "Anakapalli"];

export default function Layout() {
  const { role, fullName, logout } = useAuth();
  const navigate = useNavigate();
  const [pcName, setPcNameState] = useState("");
  const [acName, setAcNameState] = useState("");
  const [acs, setAcs] = useState<Ac[]>([]);

  useEffect(() => {
    api.get("/retrospective/acs").then((res) => setAcs(res.data));
  }, []);

  function setPcName(pc: string) {
    setPcNameState(pc);
    setAcNameState("");
  }

  function setAcName(ac: string) {
    setAcNameState(ac);
    if (ac) {
      const owner = acs.find((a) => a.ac_name === ac)?.pc_name;
      if (owner) setPcNameState(owner);
    }
  }

  function onLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-top">
          <div className="brand">
            <h1>North Andhra Livelihoods Survey</h1>
            <div className="subtitle">C-RAW India</div>
          </div>
          <div className="app-header-user">
            <span className="role-badge">{role}</span>
            <span className="topnav-name">{fullName}</span>
            <button className="primary" style={{ background: "var(--border)", color: "var(--text-primary)" }} onClick={onLogout}>
              Sign out
            </button>
          </div>
        </div>

        <div className="global-filters">
          <span className="global-filters-label">Scope</span>
          <select value={pcName} onChange={(e) => setPcName(e.target.value)}>
            <option value="">All parliamentary constituencies</option>
            {PC_NAMES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <select value={acName} onChange={(e) => setAcName(e.target.value)}>
            <option value="">All assembly constituencies</option>
            {acs
              .filter((a) => !pcName || a.pc_name === pcName)
              .map((a) => (
                <option key={a.ac_name} value={a.ac_name}>
                  {a.ac_name}
                </option>
              ))}
          </select>
          {(pcName || acName) && (
            <button
              type="button"
              className="clear-filters-btn"
              onClick={() => {
                setPcNameState("");
                setAcNameState("");
              }}
            >
              Clear
            </button>
          )}
        </div>

        <nav className="page-tabs">
          {PAGES.map((p) => (
            <NavLink key={p.to} to={p.to} className={({ isActive }) => "page-tab" + (isActive ? " active" : "")}>
              {p.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="main-content">
        <Outlet context={{ pcName, acName, setPcName, setAcName, acs }} />
      </main>
    </div>
  );
}
