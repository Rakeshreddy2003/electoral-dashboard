// Every sentence shown under a chart is computed here from the fetched
// data. Each function returns null when the data cannot support the
// statement, and the caller renders nothing in that case.

export interface WinnerRow {
  year: number;
  ac_name: string;
  candidate_name: string;
  party: string;
  vote_share_percentage: number;
  turnout_percentage: number;
}

export interface PartyYear {
  party: string;
  votes: number;
  seats: number;
  vote_share: number | null;
  seat_share: number | null;
}

export interface YearSummary {
  year: number;
  total_votes: number;
  total_seats: number;
  parties: PartyYear[];
}

export function seatCounts(winners: WinnerRow[], year: number): [string, number][] {
  const counts = new Map<string, number>();
  winners.filter((w) => w.year === year).forEach((w) => counts.set(w.party, (counts.get(w.party) ?? 0) + 1));
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function seats(n: number): string {
  return `${n} seat${n === 1 ? "" : "s"}`;
}

export function heroHeadline(winners: WinnerRow[], year: number, place: string): string | null {
  const counts = seatCounts(winners, year);
  if (counts.length === 0) return null;
  const total = counts.reduce((sum, [, n]) => sum + n, 0);
  const [topParty, topSeats] = counts[0];
  const tied = counts.filter(([, n]) => n === topSeats).map(([p]) => p);
  if (tied.length > 1) {
    return `${tied.slice(0, -1).join(", ")} and ${tied[tied.length - 1]} won ${seats(topSeats)} each of ${total} ${place} in ${year}`;
  }
  return `${topParty} won ${topSeats} of ${total} assembly ${total === 1 ? "seat" : "seats"} ${place} in ${year}`;
}

export function heroComparison(winners: WinnerRow[], year: number, prevYear: number | null): string | null {
  if (prevYear == null) return null;
  const now = seatCounts(winners, year);
  const before = seatCounts(winners, prevYear);
  if (now.length === 0 || before.length === 0) return null;
  const [topParty, topSeats] = now[0];
  const [prevTop, prevTopSeats] = before[0];
  const topBefore = before.find(([p]) => p === topParty)?.[1] ?? 0;
  if (prevTop === topParty) {
    if (topSeats === topBefore) return `Unchanged from ${prevYear}.`;
    return `${topSeats > topBefore ? "Up" : "Down"} from ${topBefore} in ${prevYear}.`;
  }
  const prevTopNow = now.find(([p]) => p === prevTop)?.[1] ?? 0;
  return `Up from ${topBefore} in ${prevYear}, when ${prevTop} led with ${prevTopSeats}. ${prevTop} won ${prevTopNow} in ${year}.`;
}

export function seatsFlipped(winners: WinnerRow[], year: number, prevYear: number | null): string | null {
  if (prevYear == null) return null;
  const before = new Map(winners.filter((w) => w.year === prevYear).map((w) => [w.ac_name, w.party]));
  const now = winners.filter((w) => w.year === year && before.has(w.ac_name));
  if (now.length === 0) return null;
  const flipped = now.filter((w) => before.get(w.ac_name) !== w.party).length;
  if (flipped === 0) return `No seat changed party between ${prevYear} and ${year}.`;
  return `${flipped} of ${now.length} seats changed party between ${prevYear} and ${year}.`;
}

export function conversionInsight(summary: YearSummary | undefined): string | null {
  if (!summary || summary.total_seats < 3) return null;
  const withShares = summary.parties.filter((p) => p.vote_share != null && p.seat_share != null);
  const over = [...withShares].sort((a, b) => b.seat_share! - b.vote_share! - (a.seat_share! - a.vote_share!))[0];
  const under = [...withShares].filter((p) => p.vote_share! >= 5).sort((a, b) => a.seat_share! - a.vote_share! - (b.seat_share! - b.vote_share!))[0];
  const parts: string[] = [];
  if (over && over.seat_share! - over.vote_share! >= 5) {
    parts.push(`${over.party} took ${over.seat_share!.toFixed(0)}% of seats on ${over.vote_share!.toFixed(1)}% of votes.`);
  }
  if (under && under.party !== over?.party && under.vote_share! - under.seat_share! >= 5) {
    parts.push(`${under.party} polled ${under.vote_share!.toFixed(1)}% and won ${seats(under.seats)}.`);
  }
  return parts.length ? parts.join(" ") : null;
}

export function turnoutInsight(trend: { year: number; avg_turnout_percentage: number | null }[]): string | null {
  const known = trend.filter((t) => t.avg_turnout_percentage != null);
  if (known.length < 2) return null;
  const first = known[0];
  const last = known[known.length - 1];
  const delta = last.avg_turnout_percentage! - first.avg_turnout_percentage!;
  const verb = delta > 0.05 ? "rose" : delta < -0.05 ? "fell" : "held steady";
  if (verb === "held steady") return `Average turnout held steady at ${last.avg_turnout_percentage!.toFixed(1)}% between ${first.year} and ${last.year}.`;
  return `Average turnout ${verb} from ${first.avg_turnout_percentage!.toFixed(1)}% in ${first.year} to ${last.avg_turnout_percentage!.toFixed(1)}% in ${last.year}, a change of ${Math.abs(delta).toFixed(1)} points.`;
}
