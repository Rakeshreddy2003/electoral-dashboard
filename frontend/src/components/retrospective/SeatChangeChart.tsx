import { partyColor } from "./partyColors";
import { YearSummary } from "./insights";

export default function SeatChangeChart({
  summary,
  previous,
  scopeLabel,
  flippedSentence,
}: {
  summary: YearSummary | undefined;
  previous: YearSummary | undefined;
  scopeLabel: string;
  flippedSentence: string | null;
}) {
  const title = summary && previous ? `Seats gained and lost, ${previous.year} to ${summary.year}` : "Seats gained and lost";

  if (!summary || !previous) {
    return (
      <div className="card">
        <h3 className="card-title">{title}</h3>
        <div className="empty-state">
          {summary ? `${summary.year} is the earliest election in this dataset, so there is no earlier result to compare it with.` : "No results loaded for this year"}
        </div>
      </div>
    );
  }

  const before = new Map(previous.parties.map((p) => [p.party, p]));
  const now = new Map(summary.parties.map((p) => [p.party, p]));
  const rows = [...new Set([...before.keys(), ...now.keys()])]
    .map((party) => {
      const from = before.get(party);
      const to = now.get(party);
      return { party, from, to, delta: (to?.seats ?? 0) - (from?.seats ?? 0) };
    })
    .filter((r) => (r.from?.seats ?? 0) > 0 || (r.to?.seats ?? 0) > 0)
    .sort((a, b) => b.delta - a.delta);
  const max = Math.max(1, ...rows.map((r) => Math.abs(r.delta)));

  return (
    <div className="card">
      <h3 className="card-title">{title}</h3>
      <p className="chart-caption">Assembly election, {scopeLabel}. Bars to the right are seats gained, bars to the left are seats lost.</p>
      {rows.length === 0 ? (
        <div className="empty-state">No seats recorded for these two elections</div>
      ) : (
        <div className="diverge-chart">
          {rows.map((r) => (
            <div key={r.party} className="diverge-row">
              <span className="diverge-name">{r.party}</span>
              <span className="diverge-track">
                <span className="diverge-half diverge-loss">
                  {r.delta < 0 && <span className="diverge-bar" style={{ width: `${(Math.abs(r.delta) / max) * 100}%`, background: partyColor(r.party) }} />}
                </span>
                <span className="diverge-half diverge-gain">
                  {r.delta > 0 && <span className="diverge-bar" style={{ width: `${(r.delta / max) * 100}%`, background: partyColor(r.party) }} />}
                </span>
              </span>
              <span className="diverge-value">
                <strong>
                  {r.delta > 0 ? "+" : r.delta < 0 ? "−" : ""}
                  {Math.abs(r.delta)}
                </strong>
                <small>
                  {r.from ? r.from.seats : `did not contest in ${previous.year}`}
                  {" to "}
                  {r.to ? r.to.seats : `did not contest in ${summary.year}`}
                </small>
              </span>
            </div>
          ))}
        </div>
      )}
      {flippedSentence && <p className="insight">{flippedSentence}</p>}
    </div>
  );
}
