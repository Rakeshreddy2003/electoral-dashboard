import { Fragment, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import ElectionTimeline, { AcDetail } from "../components/retrospective/ElectionTimeline";
import CloseContests from "../components/retrospective/CloseContests";
import CandidateDrilldown from "../components/retrospective/CandidateDrilldown";
import RetrospectiveMap from "../components/retrospective/RetrospectiveMap";
import TopCandidatesHistory from "../components/retrospective/TopCandidatesHistory";
import DemographicsCard from "../components/retrospective/DemographicsCard";
import SeatGrid, { SeatList, SeatTally, YearSwitcher } from "../components/retrospective/SeatGrid";
import VotesVsSeatsChart from "../components/retrospective/VotesVsSeatsChart";
import SeatChangeChart from "../components/retrospective/SeatChangeChart";
import { YearSummary, heroComparison, heroHeadline, seatsFlipped, sweepSentence, turnoutInsight } from "../components/retrospective/insights";
import { partyTagStyle } from "../components/retrospective/partyColors";
import { useGlobalFilters } from "../filters";

interface Winner {
  year: number;
  ac_name: string;
  candidate_name: string;
  party: string;
  vote_share_percentage: number;
  turnout_percentage: number;
}

interface PcHistoryRow {
  year: number;
  candidate_name: string;
  party: string;
  position: number;
  votes: number;
  vote_share_percentage: number;
  turnout_percentage: number;
  total_electors: number;
}

export default function Retrospective() {
  const { pcName, acName, setPcName, setAcName, acs } = useGlobalFilters();
  // Cross-filter: click a party name in the votes-vs-seats chart, or a seat
  // in the hero grid, to filter the winning-candidates table and the
  // close-contest list by it -- the same click-to-filter contract Form
  // Responses already has.
  const [partyFilter, setPartyFilter] = useState<string | null>(null);
  const [winners, setWinners] = useState<Winner[]>([]);
  const [turnoutTrend, setTurnoutTrend] = useState<{ year: number; avg_turnout_percentage: number | null }[]>([]);
  const [pcHistory, setPcHistory] = useState<PcHistoryRow[]>([]);
  const [acDetail, setAcDetail] = useState<AcDetail | null>(null);
  const [partySummary, setPartySummary] = useState<YearSummary[]>([]);
  const [pickedYear, setPickedYear] = useState<number | null>(null);

  useEffect(() => {
    // A fast response to a later, narrower request (e.g. picking an AC
    // right after a PC) can arrive before a slower, wider one still in
    // flight -- without this guard the wider response would land last and
    // overwrite the correct, narrower state.
    let current = true;
    const params: Record<string, string> = {};
    if (acName) params.ac_name = acName;
    else if (pcName) params.pc_name = pcName;

    api.get("/retrospective/winners-by-year", { params }).then((res) => current && setWinners(res.data));
    api.get("/retrospective/turnout-trend", { params: pcName ? { pc_name: pcName } : {} }).then((res) => current && setTurnoutTrend(res.data));
    api.get("/retrospective/party-summary", { params: pcName ? { pc_name: pcName } : {} }).then((res) => current && setPartySummary(res.data));
    return () => {
      current = false;
    };
  }, [pcName, acName]);

  useEffect(() => {
    let current = true;
    if (!pcName) {
      setPcHistory([]);
      return;
    }
    api.get("/retrospective/pc-history", { params: { pc_name: pcName } }).then((res) => current && setPcHistory(res.data));
    return () => {
      current = false;
    };
  }, [pcName]);

  useEffect(() => {
    let current = true;
    if (!acName) {
      setAcDetail(null);
      return;
    }
    api.get("/retrospective/ac-detail", { params: { ac_name: acName } }).then((res) => current && setAcDetail(res.data));
    return () => {
      current = false;
    };
  }, [acName]);

  // Group the flat winners-by-year rows by AC (newest year first within
  // each group) so the table reads as "35 AC blocks of 4 years" instead of
  // 140 same-looking rows where which AC a row belongs to is only visible
  // by re-reading the AC column on every row.
  const winnerGroups = useMemo(() => {
    const filtered = partyFilter ? winners.filter((w) => w.party === partyFilter) : winners;
    const byAc = new Map<string, Winner[]>();
    filtered.forEach((w) => {
      const group = byAc.get(w.ac_name) ?? [];
      group.push(w);
      byAc.set(w.ac_name, group);
    });
    return [...byAc.entries()].map(([ac_name, rows]) => ({
      ac_name,
      rows: [...rows].sort((a, b) => b.year - a.year),
    }));
  }, [winners, partyFilter]);

  const years = useMemo(() => [...new Set(winners.map((w) => w.year))].sort(), [winners]);
  const year = pickedYear != null && years.includes(pickedYear) ? pickedYear : years[years.length - 1];
  const prevYear = years[years.indexOf(year) - 1] ?? null;
  const summary = partySummary.find((s) => s.year === year);
  const prevSummary = partySummary.find((s) => s.year === prevYear);

  const latestPcWinner = pcHistory.filter((r) => r.position === 1).sort((a, b) => b.year - a.year)[0];
  const scopeLabel = pcName ? `${pcName} parliamentary constituency` : "all of North Andhra";
  const acLatest = acName ? [...winners].sort((a, b) => b.year - a.year)[0] : null;

  const headline = acName
    ? acLatest
      ? `${acLatest.candidate_name} of ${acLatest.party} won ${acName} in ${acLatest.year} with ${acLatest.vote_share_percentage?.toFixed(1)}% of the vote`
      : null
    : year != null
    ? heroHeadline(winners, year, pcName ? `in ${pcName}` : "across North Andhra")
    : null;
  const comparison = !acName && year != null ? heroComparison(winners, year, prevYear) : null;

  return (
    <>
      <section className="hero">
        <div className="hero-main">
          <p className="hero-label">
            {acName ? `${acName} assembly constituency` : pcName ? `${pcName} parliamentary constituency` : "North Andhra"}, assembly elections {years[0]} to{" "}
            {years[years.length - 1]}
          </p>
          {headline ? <h2 className="hero-headline">{headline}</h2> : <h2 className="hero-headline">Loading results</h2>}
          <p className="hero-sub">
            {comparison}
            {acName && acDetail?.pc_name ? `Part of ${acDetail.pc_name} parliamentary constituency.` : ""}
            {!acName && pcName && latestPcWinner
              ? ` Its Lok Sabha seat went to ${latestPcWinner.candidate_name} of ${latestPcWinner.party} in ${latestPcWinner.year}.`
              : ""}
          </p>

          {acName ? (
            <SeatList
              rows={[...winners]
                .sort((a, b) => b.year - a.year)
                .map((w) => ({ key: `${w.ac_name}-${w.year}`, label: String(w.year), winner: w }))}
            />
          ) : year != null ? (
            <>
              <div className="hero-controls">
                <YearSwitcher years={years} year={year} onChange={setPickedYear} />
                <SeatTally winners={winners} year={year} />
              </div>
              {pcName ? (
                <SeatList
                  rows={winners
                    .filter((w) => w.year === year)
                    .map((w) => ({ key: w.ac_name, label: w.ac_name, winner: w, select: w.ac_name }))}
                  onSelect={setAcName}
                />
              ) : (
                <SeatGrid winners={winners} year={year} acs={acs} onSelectAc={setAcName} onSelectPc={setPcName} />
              )}
              <ul className="hero-takeaways">
                {[seatsFlipped(winners, year, prevYear), pcName ? null : sweepSentence(winners, new Map(acs.map((a) => [a.ac_name, a.pc_name ?? ""])), year)]
                  .filter(Boolean)
                  .map((t) => (
                    <li key={t}>{t}</li>
                  ))}
              </ul>
            </>
          ) : null}
        </div>

        <div className="hero-map">
          <RetrospectiveMap selectedPc={pcName} onSelectPc={setPcName} onSelectAc={setAcName} />
        </div>
      </section>

      {acName && acDetail ? (
        <>
          <ElectionTimeline detail={acDetail} />
          <TopCandidatesHistory acName={acName} title={`${acName}: top three candidates in each assembly election`} />
          <CandidateDrilldown acName={acName} years={acDetail.timeline.map((t) => t.year)} />
          <DemographicsCard acName={acName} />
        </>
      ) : pcName ? (
        <>
          <div className="card">
            <h3>Lok Sabha results — {pcName}</h3>
            {pcHistory.filter((r) => r.position === 1).length === 0 ? (
              <div className="empty-state">No data yet</div>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Year</th>
                      <th>Winning MP</th>
                      <th>Party</th>
                      <th className="num">Vote share %</th>
                      <th className="num">Turnout %</th>
                      <th className="num">Electors</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pcHistory
                      .filter((r) => r.position === 1)
                      .sort((a, b) => b.year - a.year)
                      .map((r, i) => (
                        <tr key={i}>
                          <td style={{ fontWeight: 600 }}>{r.year}</td>
                          <td>{r.candidate_name}</td>
                          <td>
                            <span className="party-tag" style={partyTagStyle(r.party)}>
                              {r.party}
                            </span>
                          </td>
                          <td className="num">{r.vote_share_percentage?.toFixed(1)}</td>
                          <td className="num">{r.turnout_percentage?.toFixed(1)}</td>
                          <td className="num">{r.total_electors?.toLocaleString()}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          <TopCandidatesHistory pcName={pcName} title={`${pcName}: top three candidates in each Lok Sabha election`} />
          <DemographicsCard pcName={pcName} />
        </>
      ) : (
        <DemographicsCard />
      )}

      {!acName && (
        <>
          <div className="section-head">
            <h3>Party landscape</h3>
            <p>How many seats each party held, and how that vote share converted into seats, in {scopeLabel}.</p>
          </div>

          <div className="grid cols-2">
            <VotesVsSeatsChart summary={summary} scopeLabel={scopeLabel} activeParty={partyFilter} onPartyClick={(p) => setPartyFilter(partyFilter === p ? null : p)} />
            <SeatChangeChart summary={summary} previous={prevSummary} scopeLabel={scopeLabel} flippedSentence={seatsFlipped(winners, year, prevYear)} />
          </div>

          {turnoutInsight(turnoutTrend) && <p className="insight insight-standalone">{turnoutInsight(turnoutTrend)}</p>}

          <div className={`cross-filter-bar${!partyFilter ? " empty" : ""}`}>
            {partyFilter ? (
              <>
                <span className="filter-chip">
                  Party: {partyFilter}
                  <button type="button" onClick={() => setPartyFilter(null)} title="Remove">
                    ×
                  </button>
                </span>
                <button type="button" className="clear-filters-btn" onClick={() => setPartyFilter(null)}>
                  Clear
                </button>
              </>
            ) : (
              "Click a party above, or a seat in the grid, to filter the winning-candidates table and close contests by it."
            )}
          </div>
        </>
      )}

      {!acName && !pcName && (
        <div className="card" style={{ marginTop: 20, marginBottom: 20 }}>
          <h3>Winning candidates by year (assembly / AC level){partyFilter ? ` — ${partyFilter} wins` : ""}</h3>
          {winners.length === 0 ? (
            <div className="empty-state">No data yet — run the ECI ETL loader (backend/etl/load_eci_data.py)</div>
          ) : (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Year</th>
                    <th>AC</th>
                    <th>Winner</th>
                    <th>Party</th>
                    <th className="num">Vote share %</th>
                    <th className="num">Turnout %</th>
                  </tr>
                </thead>
                <tbody>
                  {winnerGroups.map((group, gi) => (
                    <Fragment key={group.ac_name}>
                      {group.rows.map((w, i) => (
                        <tr key={`${group.ac_name}-${w.year}`} className={gi % 2 === 1 ? "row-group-shaded" : undefined}>
                          <td style={{ fontWeight: 600 }}>{w.year}</td>
                          {i === 0 ? (
                            <td rowSpan={group.rows.length} style={{ fontWeight: 700, verticalAlign: "top", borderRight: "1px solid var(--border)" }}>
                              {group.ac_name}
                            </td>
                          ) : null}
                          <td>{w.candidate_name}</td>
                          <td>
                            <span className="party-tag" style={partyTagStyle(w.party)}>
                              {w.party}
                            </span>
                          </td>
                          <td className="num">{w.vote_share_percentage?.toFixed(1)}</td>
                          <td className="num">{w.turnout_percentage?.toFixed(1)}</td>
                        </tr>
                      ))}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div style={{ marginTop: 20 }}>
        <CloseContests pcName={pcName} party={partyFilter} />
      </div>

    </>
  );
}
