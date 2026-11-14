import { useState } from "react";
import { Ac } from "../../filters";
import { partyColor, partyTagStyle } from "./partyColors";
import { WinnerRow, seatCounts } from "./insights";

export function YearSwitcher({ years, year, onChange }: { years: number[]; year: number; onChange: (y: number) => void }) {
  return (
    <div className="year-switcher" role="group" aria-label="Election year">
      {years.map((y) => (
        <button key={y} type="button" aria-pressed={y === year} onClick={() => onChange(y)}>
          {y}
        </button>
      ))}
    </div>
  );
}

export function SeatTally({ winners, year }: { winners: WinnerRow[]; year: number }) {
  return (
    <ul className="seat-tally">
      {seatCounts(winners, year).map(([party, n]) => (
        <li key={party}>
          <span className="seat-swatch" style={{ background: partyColor(party) }} />
          {party} <strong>{n}</strong>
        </li>
      ))}
    </ul>
  );
}

// One square per assembly seat, one row per parliamentary constituency.
// Seats keep the same position in every year so switching year shows
// which squares changed colour.
export default function SeatGrid({
  winners,
  year,
  acs,
  onSelectAc,
  onSelectPc,
}: {
  winners: WinnerRow[];
  year: number;
  acs: Ac[];
  onSelectAc: (ac: string) => void;
  onSelectPc: (pc: string) => void;
}) {
  const [hovered, setHovered] = useState<WinnerRow | null>(null);
  const byAc = new Map(winners.filter((w) => w.year === year).map((w) => [w.ac_name, w]));
  const pcOf = new Map(acs.map((a) => [a.ac_name, a.pc_name ?? "Other"]));
  const groups = new Map<string, string[]>();
  [...new Set(winners.map((w) => w.ac_name))].sort().forEach((ac) => {
    const pc = pcOf.get(ac) ?? "Other";
    groups.set(pc, [...(groups.get(pc) ?? []), ac]);
  });

  return (
    <div>
      <div className="seat-grid">
        {[...groups.entries()].map(([pc, names]) => (
          <div key={pc} className="seat-row">
            <button type="button" className="seat-row-name" onClick={() => onSelectPc(pc)} title={`Show ${pc} only`}>
              {pc}
            </button>
            <div className="seat-row-squares">
              {names.map((ac) => {
                const w = byAc.get(ac);
                return (
                  <button
                    key={ac}
                    type="button"
                    className="seat"
                    style={{ background: w ? partyColor(w.party) : "transparent" }}
                    aria-label={w ? `${ac}: ${w.candidate_name}, ${w.party}, ${year}` : `${ac}: no result for ${year}`}
                    onMouseEnter={() => setHovered(w ?? null)}
                    onFocus={() => setHovered(w ?? null)}
                    onMouseLeave={() => setHovered(null)}
                    onBlur={() => setHovered(null)}
                    onClick={() => onSelectAc(ac)}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <p className="seat-readout" aria-live="polite">
        {hovered
          ? `${hovered.ac_name}: ${hovered.candidate_name} (${hovered.party}), ${hovered.vote_share_percentage?.toFixed(1)}% of the vote`
          : "Each square is one assembly seat. Point at a seat for its result, or select it to open that constituency."}
      </p>
    </div>
  );
}

export function SeatList({ rows, onSelect }: { rows: { key: string; label: string; winner: WinnerRow; select?: string }[]; onSelect?: (ac: string) => void }) {
  return (
    <ul className="seat-list">
      {rows.map((r) => (
        <li key={r.key}>
          <span className="seat-swatch" style={{ background: partyColor(r.winner.party) }} />
          {onSelect && r.select ? (
            <button type="button" className="seat-list-name" onClick={() => onSelect(r.select!)}>
              {r.label}
            </button>
          ) : (
            <span className="seat-list-name">{r.label}</span>
          )}
          <span className="seat-list-winner">{r.winner.candidate_name}</span>
          <span className="party-tag" style={partyTagStyle(r.winner.party)}>
            {r.winner.party}
          </span>
          <span className="seat-list-share">{r.winner.vote_share_percentage?.toFixed(1)}%</span>
        </li>
      ))}
    </ul>
  );
}
