import { partyColor } from "./partyColors";
import { YearSummary, conversionInsight } from "./insights";

const MIN_VOTE_SHARE = 3;

export default function VotesVsSeatsChart({
  summary,
  scopeLabel,
  activeParty,
  onPartyClick,
}: {
  summary: YearSummary | undefined;
  scopeLabel: string;
  activeParty?: string | null;
  onPartyClick?: (party: string) => void;
}) {
  const shown = (summary?.parties ?? []).filter((p) => p.seats > 0 || (p.vote_share ?? 0) >= MIN_VOTE_SHARE);
  const rest = (summary?.parties ?? []).filter((p) => !shown.includes(p));
  const restVotes = rest.reduce((sum, p) => sum + (p.vote_share ?? 0), 0);
  const insight = conversionInsight(summary);

  return (
    <div className="card">
      <h3 className="card-title">Share of votes against share of seats{summary ? `, ${summary.year}` : ""}</h3>
      <p className="chart-caption">Assembly election, {scopeLabel}. A party whose seat bar is longer than its vote bar won more seats than its vote share alone would give.</p>
      {!summary || shown.length === 0 ? (
        <div className="empty-state">No results loaded for this year</div>
      ) : (
        <>
          <div className="pair-chart" role="table" aria-label="Vote share and seat share by party">
            <div className="pair-row pair-head" role="row">
              <span role="columnheader">Party</span>
              <span role="columnheader">Votes</span>
              <span role="columnheader">Seats</span>
            </div>
            {shown.map((p) => (
              <div key={p.party} className={`pair-row${activeParty === p.party ? " pair-row-active" : ""}`} role="row">
                <span role="cell">
                  {onPartyClick ? (
                    <button type="button" className="pair-name pair-name-btn" onClick={() => onPartyClick(p.party)}>
                      {p.party}
                    </button>
                  ) : (
                    <span className="pair-name">{p.party}</span>
                  )}
                </span>
                <span className="pair-cell" role="cell">
                  <span className="pair-track">
                    <span className="pair-bar" style={{ width: `${p.vote_share ?? 0}%`, background: partyColor(p.party) }} />
                  </span>
                  <span className="pair-value">{(p.vote_share ?? 0).toFixed(1)}%</span>
                </span>
                <span className="pair-cell" role="cell">
                  <span className="pair-track">
                    <span className="pair-bar" style={{ width: `${p.seat_share ?? 0}%`, background: partyColor(p.party) }} />
                  </span>
                  <span className="pair-value">
                    {(p.seat_share ?? 0).toFixed(0)}% <small>({p.seats})</small>
                  </span>
                </span>
              </div>
            ))}
          </div>
          {rest.length > 0 && (
            <p className="chart-footnote">
              {rest.length} other {rest.length === 1 ? "party or independent group" : "parties and independents"} together polled {restVotes.toFixed(1)}% and won no seat.
            </p>
          )}
          {insight && <p className="insight">{insight}</p>}
        </>
      )}
    </div>
  );
}
