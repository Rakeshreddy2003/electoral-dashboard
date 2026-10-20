import { Fragment, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import GroupedBarChartCard from "../components/charts/GroupedBarChartCard";
import StatTile from "../components/charts/StatTile";
import PageHeader from "../components/PageHeader";
import ElectionTimeline, { AcDetail } from "../components/retrospective/ElectionTimeline";
import CloseContests from "../components/retrospective/CloseContests";
import CandidateDrilldown from "../components/retrospective/CandidateDrilldown";
import RetrospectiveMap from "../components/retrospective/RetrospectiveMap";
import TopCandidatesHistory from "../components/retrospective/TopCandidatesHistory";
import DemographicsCard from "../components/retrospective/DemographicsCard";
import { partyColor } from "../components/retrospective/partyColors";
import { useGlobalFilters } from "../filters";

const MAX_PARTY_SERIES = 6; // past this, fold into "Other" -- see dataviz anti-patterns (>7 color classes blur)

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
  // Cross-filter: click a party's bar in the seats-by-year chart to filter
  // the winning-candidates table and the close-contest list by it, the
  // same click-to-filter contract Form Responses already has.
  const [partyFilter, setPartyFilter] = useState<string | null>(null);
  const [winners, setWinners] = useState<Winner[]>([]);
  const [turnoutTrend, setTurnoutTrend] = useState<{ year: number; avg_turnout_percentage: number | null }[]>([]);
  const [pcHistory, setPcHistory] = useState<PcHistoryRow[]>([]);
  const [acDetail, setAcDetail] = useState<AcDetail | null>(null);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (acName) params.ac_name = acName;
    else if (pcName) params.pc_name = pcName;

    api.get("/retrospective/winners-by-year", { params }).then((res) => setWinners(res.data));
    api.get("/retrospective/turnout-trend", { params: pcName ? { pc_name: pcName } : {} }).then((res) => setTurnoutTrend(res.data));
  }, [pcName, acName]);

  useEffect(() => {
    if (!pcName) {
      setPcHistory([]);
      return;
    }
    api.get("/retrospective/pc-history", { params: { pc_name: pcName } }).then((res) => setPcHistory(res.data));
  }, [pcName]);

  useEffect(() => {
    if (!acName) {
      setAcDetail(null);
      return;
    }
    api.get("/retrospective/ac-detail", { params: { ac_name: acName } }).then((res) => setAcDetail(res.data));
  }, [acName]);

  // Seats won by party, split by year -- a flat all-years total hides which
  // party is currently ahead; small-party tail folds into "Other" past
  // MAX_PARTY_SERIES so the chart stays legible (dataviz anti-patterns).
  const { seatsByYear, partySeriesKeys } = useMemo(() => {
    const years = [...new Set(winners.map((w) => w.year))].sort();
    const totalsByParty = new Map<string, number>();
    winners.forEach((w) => totalsByParty.set(w.party, (totalsByParty.get(w.party) || 0) + 1));
    const topParties = [...totalsByParty.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, MAX_PARTY_SERIES)
      .map(([p]) => p);
    const hasOther = totalsByParty.size > topParties.length;

    const rows = years.map((year) => {
      const row: Record<string, number | string> = { year };
      topParties.forEach((p) => (row[p] = 0));
      if (hasOther) row["Other"] = 0;
      winners
        .filter((w) => w.year === year)
        .forEach((w) => {
          const key = topParties.includes(w.party) ? w.party : "Other";
          row[key] = (row[key] as number) + 1;
        });
      return row;
    });
    return { seatsByYear: rows, partySeriesKeys: hasOther ? [...topParties, "Other"] : topParties };
  }, [winners]);

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

  const latestYear = turnoutTrend.length ? turnoutTrend[turnoutTrend.length - 1] : null;
  const earliestYear = turnoutTrend.length ? turnoutTrend[0] : null;
  const turnoutDelta =
    latestYear?.avg_turnout_percentage != null && earliestYear?.avg_turnout_percentage != null
      ? +(latestYear.avg_turnout_percentage - earliestYear.avg_turnout_percentage).toFixed(1)
      : null;

  const latestPcWinner = pcHistory.filter((r) => r.position === 1).sort((a, b) => b.year - a.year)[0];
  const acsInPc = pcName ? acs.filter((a) => a.pc_name === pcName).length : 0;

  return (
    <>
      <PageHeader
        title="Retrospective Data"
        accent="Data"
        subtitle="Historical election results and demographic baseline across North Andhra's 5 parliamentary constituencies, 2009–2024."
      />

      {/* Basic information left, map right -- and the left side only shows
          what actually has data for the current scope: a region-wide
          summary with nothing selected, the PC's latest MP result once a
          PC is picked, the AC's latest result once an AC is picked. */}
      {/* align-items: stretch here, overriding the grid default -- an
          "at a glance" card is inherently short content, and letting it
          sit short next to a tall map either left page-background showing
          below it (default align-items: start) or stretched the card with
          nothing to fill the extra height (default stretch, no centering).
          Stretching AND centering the content together is what actually
          uses the space instead of just moving where it's empty. */}
      <div className="grid cols-2" style={{ alignItems: "stretch" }}>
        <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
          <h3>{acName ? `${acName} — at a glance` : pcName ? `${pcName} — at a glance` : "North Andhra — at a glance"}</h3>
          {acName && acDetail ? (
            <>
              <div className="stat-tile stat-tile-brand" >
                <div className="value" style={{ fontSize: 28 }}>
                  {acDetail.timeline[acDetail.timeline.length - 1]?.winner_name ?? "—"}
                </div>
                <div className="label">Winner, {acDetail.timeline[acDetail.timeline.length - 1]?.year}</div>
              </div>
              <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)" }}>
                Part of {acDetail.pc_name ?? "—"} parliamentary constituency. See the full election timeline and demographic
                baseline below.
              </p>
            </>
          ) : pcName ? (
            <>
              <div className="stat-tile stat-tile-brand" >
                <div className="value" style={{ fontSize: 28 }}>
                  {latestPcWinner?.candidate_name ?? "—"}
                </div>
                <div className="label">
                  Lok Sabha winner, {latestPcWinner?.year ?? "—"}
                  {latestPcWinner?.party ? ` · ${latestPcWinner.party}` : ""}
                </div>
              </div>
              <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)" }}>
                {acsInPc} assembly segments tracked in {pcName}. Lok Sabha results, demographic baseline and assembly history
                below.
              </p>
            </>
          ) : turnoutDelta !== null ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <StatTile
                label={`Turnout change, ${earliestYear?.year}→${latestYear?.year}`}
                value={`${turnoutDelta > 0 ? "+" : ""}${turnoutDelta} pp`}
                tone={turnoutDelta >= 0 ? "good" : "bad"}
              />
              <div style={{ display: "flex", gap: 16 }}>
                <StatTile label="Assembly seats" value={35} tone="neutral" fill />
                <StatTile label="Parliamentary seats" value={5} tone="neutral" fill />
              </div>
            </div>
          ) : (
            <div className="empty-state">No data yet</div>
          )}
        </div>

        <div className="card">
          <h3>Constituency map</h3>
          <RetrospectiveMap selectedPc={pcName} onSelectPc={setPcName} onSelectAc={setAcName} />
        </div>
      </div>

      {acName && acDetail ? (
        <>
          <ElectionTimeline detail={acDetail} />
          <DemographicsCard acName={acName} />
          <TopCandidatesHistory acName={acName} title={`${acName} — historical top 3 candidates (assembly election)`} />
          <CandidateDrilldown acName={acName} years={acDetail.timeline.map((t) => t.year)} />
        </>
      ) : pcName ? (
        <>
          <div className="card" style={{ marginTop: 20, marginBottom: 20 }}>
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
                      .map((r, i) => (
                        <tr key={i}>
                          <td style={{ fontWeight: 600 }}>{r.year}</td>
                          <td>{r.candidate_name}</td>
                          <td>
                            <span className="party-tag" style={{ background: partyColor(r.party) }}>
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
          <DemographicsCard pcName={pcName} />
          <TopCandidatesHistory pcName={pcName} title={`${pcName} — historical top 3 candidates (Lok Sabha)`} />
        </>
      ) : (
        <DemographicsCard />
      )}

      <h3 style={{ margin: "28px 0 14px" }}>Historical data</h3>

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
          "Click a party's bar below to filter the winning-candidates table and close contests by it."
        )}
      </div>

      {/* Region-wide seat composition by year makes sense with no AC
          selected (comparing how many of the 35, or of one PC's 7, seats
          each party held) -- at AC level it degenerates into a trivial
          0-or-1-seat bar per party per year, which is what prompted "I
          don't understand the need of this." The AC's own election
          history is already covered better by ElectionTimeline (above)
          and CandidateDrilldown's per-year vote-share chart, so this
          chart is simply not shown once an AC is picked, rather than
          shown in a form that doesn't carry information at that level. */}
      {!acName && (
        <GroupedBarChartCard
          title="Assembly seats won by party, by year"
          caption={`Assembly constituency results, 2009–2024${pcName ? ` — ${pcName}` : " (all 5 PCs, 35 ACs)"}`}
          data={seatsByYear}
          xKey="year"
          seriesKeys={partySeriesKeys}
          colorFor={(key) => (key === "Other" ? "var(--text-muted)" : partyColor(key))}
          onSeriesClick={(key) => key !== "Other" && setPartyFilter(partyFilter === key ? null : key)}
          activeKey={partyFilter}
        />
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
                            <span className="party-tag" style={{ background: partyColor(w.party) }}>
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
