import { partyTagStyle } from "./partyColors";

export interface TimelineYear {
  year: number;
  winner_name: string;
  party: string;
  vote_share_percentage: number;
  margin: number | null;
  margin_percentage: number;
  turnout_percentage: number;
  total_electors: number;
  candidate_count: number;
}

interface SwingParty {
  party: string;
  swing_pp: number;
}

export interface AcDetail {
  ac_name: string;
  pc_name: string | null;
  timeline: TimelineYear[];
  swing: { from_year: number; to_year: number; by_party: SwingParty[] } | null;
  pc_latest: {
    year: number;
    candidate_name: string;
    party: string;
    vote_share_percentage: number;
    turnout_percentage: number;
    total_electors: number;
  } | null;
  electors_comparison: { ae_year: number; ae_electors: number; ge_year: number; ge_electors: number } | null;
}

export default function ElectionTimeline({ detail }: { detail: AcDetail }) {
  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3>{detail.ac_name} — Election Timeline</h3>

      {detail.swing && (
        <p style={{ margin: "0 0 14px" }}>
          <span style={{ fontSize: 12, color: "var(--text-muted)", marginRight: 8 }}>
            Vote-share swing {detail.swing.from_year} → {detail.swing.to_year}:
          </span>
          {detail.swing.by_party
            .filter((s) => Math.abs(s.swing_pp) >= 0.5)
            .slice(0, 6)
            .map((s) => (
              <span key={s.party} className={`swing-badge ${s.swing_pp >= 0 ? "swing-up" : "swing-down"}`}>
                {s.party} {s.swing_pp >= 0 ? "+" : ""}
                {s.swing_pp}pp
              </span>
            ))}
        </p>
      )}

      <div className="timeline-row">
        {detail.timeline.map((t) => (
          <div key={t.year} className="timeline-node">
            <div className="yr">{t.year} (Assembly)</div>
            <div className="winner">{t.winner_name}</div>
            <span className="party-tag" style={partyTagStyle(t.party)}>
              {t.party}
            </span>
            <div className="meta">
              Vote share: <strong>{t.vote_share_percentage?.toFixed(1)}%</strong>
              <br />
              Margin: <strong>{t.margin_percentage?.toFixed(1)}%</strong>
              {t.margin != null && ` (${t.margin.toLocaleString()} votes)`}
              <br />
              Turnout: <strong>{t.turnout_percentage?.toFixed(1)}%</strong>
              <br />
              {t.candidate_count} candidates contested
            </div>
          </div>
        ))}

        {detail.pc_latest && (
          <div className="timeline-node" style={{ background: "var(--surface-1)", borderStyle: "dashed" }}>
            <div className="yr">{detail.pc_latest.year} (Lok Sabha — {detail.pc_name})</div>
            <div className="winner">{detail.pc_latest.candidate_name}</div>
            <span className="party-tag" style={partyTagStyle(detail.pc_latest.party)}>
              {detail.pc_latest.party}
            </span>
            <div className="meta">
              MP for the whole {detail.pc_name} parliamentary seat, not this AC alone.
              <br />
              Vote share: <strong>{detail.pc_latest.vote_share_percentage?.toFixed(1)}%</strong>
              <br />
              Turnout: <strong>{detail.pc_latest.turnout_percentage?.toFixed(1)}%</strong>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
