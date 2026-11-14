import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import BarChartCard from "../components/charts/BarChartCard";
import DonutChartCard from "../components/charts/DonutChartCard";
import StatTile from "../components/charts/StatTile";
import MapView, { MapPoint } from "../components/MapView";
import PageHeader from "../components/PageHeader";
import { formatINR } from "../format";
import { useGlobalFilters } from "../filters";

// Below this, a single outlier answer can swing the whole bar -- see the
// earnings-by-occupation chart below.
const MIN_EARNINGS_SAMPLE = 3;

// {name, code, count}[] -> {name, code, pct}[] for the donut charts --
// low-cardinality share-of-whole breakdowns (gender, yes/no) read better as
// a donut than a bar; high-cardinality rankings (occupation, priorities)
// stay as horizontal bars, where donuts would turn into an unreadable ring
// of slivers.
function toPctData(items: Named[]): { name: string; code?: string | null; pct: number; count: number }[] {
  const total = items.reduce((sum, d) => sum + d.count, 0);
  return items.map((d) => ({ name: d.name, code: d.code, pct: total ? Math.round((d.count / total) * 1000) / 10 : 0, count: d.count }));
}

// Display name for each cross-filterable field, used in the chip bar.
const FIELD_LABELS: Record<string, string> = {
  pc_name: "Constituency",
  occupation: "Occupation",
  gender: "Gender",
  age_group: "Age group",
  education: "Education",
  employment_arrangement: "Employment",
  has_second_income: "2nd income",
  top_priority_problem: "Priority",
  scheme_awareness: "Scheme awareness",
  healthcare_access: "Healthcare access",
  schooling_access: "Schooling access",
  emergency_line_usage: "Emergency line use",
};

interface Named {
  name: string;
  code?: string | null;
  count: number;
}

interface Summary {
  total_responses: number;
  by_constituency: Named[];
  by_occupation: Named[];
  by_gender: Named[];
  by_age_group: Named[];
  by_education: Named[];
  by_employment_arrangement: Named[];
  by_second_income: Named[];
}

interface Political {
  by_priority_problem: Named[];
  by_trust_score: { score: number; count: number }[];
  by_scheme_awareness: Named[];
  by_healthcare_access: Named[];
  by_schooling_access: Named[];
  by_emergency_line_usage: Named[];
}

interface Stats {
  count: number;
  median: number | null;
  mean: number | null;
}

interface EarningsByOccupation extends Stats {
  occupation: string;
  occupation_code: string | null;
}

interface Livelihood {
  respondents_with_livelihood_data: number;
  earnings: Stats;
  earnings_by_occupation: EarningsByOccupation[];
  expenses: Stats;
  pay_late_months: Stats;
  scheme_funnel: { eligible_modules_n: number; aware_n: number; applied_n: number; received_n: number };
  top_risk_incidents: Named[];
  respondents_with_risk_data: number;
  top_skills_held: Named[];
  respondents_with_skill_data: number;
}

function pct(part: number | undefined, whole: number | undefined): number | null {
  if (!part || !whole) return null;
  return Math.round((part / whole) * 100);
}

export default function Responses() {
  // pc_name/ac_name come from the shared header scope, not local state --
  // the chip-filter system below stays page-local (occupation, gender,
  // etc. don't make sense as global scope the way a constituency does).
  const { pcName, acName } = useGlobalFilters();
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [chipLabels, setChipLabels] = useState<Record<string, string>>({});
  const [summary, setSummary] = useState<Summary | null>(null);
  const [political, setPolitical] = useState<Political | null>(null);
  const [livelihood, setLivelihood] = useState<Livelihood | null>(null);
  const [points, setPoints] = useState<MapPoint[]>([]);

  const params = useMemo(
    () => ({ ...filters, ...(pcName && { pc_name: pcName }), ...(acName && { ac_name: acName }) }),
    [filters, pcName, acName]
  );

  useEffect(() => {
    api.get("/responses/summary", { params }).then((res) => setSummary(res.data));
    api.get("/responses/political", { params }).then((res) => setPolitical(res.data));
    api.get("/responses/livelihood", { params }).then((res) => setLivelihood(res.data));
    api.get("/responses/map-points", { params }).then((res) => setPoints(res.data));
  }, [params]);

  // Click a bar to filter every chart on the page by that value; click the
  // same bar again (or its chip) to remove the filter. Several filters
  // combine with AND. Inspired by the UK (ukac) dashboard's cross-filter
  // pattern -- click a slice/row/cell, every view re-renders against the
  // same slice, a chip bar shows and lets you remove what's active.
  function toggleFilter(field: string, code: string | null | undefined, label: string) {
    if (!code) return;
    setFilters((prev) => {
      if (prev[field] === code) {
        const next = { ...prev };
        delete next[field];
        return next;
      }
      return { ...prev, [field]: code };
    });
    setChipLabels((prev) => {
      if (prev[field] && filters[field] === code) {
        const next = { ...prev };
        delete next[field];
        return next;
      }
      return { ...prev, [field]: `${FIELD_LABELS[field] ?? field}: ${label}` };
    });
  }

  function removeFilter(field: string) {
    setFilters((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
    setChipLabels((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }

  function clearFilters() {
    setFilters({});
    setChipLabels({});
  }

  const topOccupation = summary?.by_occupation[0];
  const topOccupationPct = pct(topOccupation?.count, summary?.total_responses);
  const topPriority = political?.by_priority_problem[0];
  const topPriorityPct = pct(topPriority?.count, summary?.total_responses);
  const knownGender = (summary?.by_gender ?? []).filter((g) => g.code !== null && g.name !== "Unknown");
  const genderTotal = knownGender.reduce((s, g) => s + g.count, 0);
  const malePct = pct(knownGender.find((g) => g.code === "male")?.count, genderTotal);
  const schemeAwareN = livelihood?.scheme_funnel.aware_n ?? 0;
  const schemeEligibleN = livelihood?.scheme_funnel.eligible_modules_n ?? 0;
  const schemeAwarePct = pct(schemeAwareN, schemeEligibleN);

  const chipKeys = Object.keys(chipLabels);

  return (
    <>
      <PageHeader
        title="Form Responses"
        accent="Responses"
        subtitle="Live survey analytics from the North Andhra Livelihoods Survey, synced from ODK Central."
      />

      <div className={`cross-filter-bar${chipKeys.length === 0 ? " empty" : ""}`}>
        {chipKeys.length === 0 ? (
          "Click a bar in any chart below to filter every chart on this page by it."
        ) : (
          <>
            {chipKeys.map((field) => (
              <span className="filter-chip" key={field}>
                {chipLabels[field]}
                <button type="button" onClick={() => removeFilter(field)} title="Remove">
                  ×
                </button>
              </span>
            ))}
            <button type="button" className="clear-filters-btn" onClick={clearFilters}>
              Clear all
            </button>
          </>
        )}
      </div>

      {/* The executive-summary block: distinct from the chart cards below it
          via a tinted surface and a slightly larger/bolder heading, not a
          colored accent bar (a border-left above 1px on a callout is the
          generic-dashboard "look, this one's important" crutch) and not by
          being oversized. */}
      <div
        className="card"
        style={{
          marginBottom: 24,
          background: "color-mix(in srgb, var(--series-1) 4%, var(--surface-1))",
        }}
      >
        <h3
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 16,
            fontWeight: 800,
            textTransform: "none",
            letterSpacing: "-0.01em",
            color: "var(--text-primary)",
            marginBottom: 14,
          }}
        >
          Key findings {acName ? `— ${acName}` : pcName ? `— ${pcName}` : "— all 5 constituencies"}
        </h3>
        <div className="grid cols-2" style={{ gap: 10 }}>
          <p style={{ margin: 0, fontSize: 14 }}>
            <strong>{summary?.total_responses ?? "—"}</strong> responses match the current filters, across{" "}
            <strong>{summary?.by_constituency.length ?? "—"}</strong> constituencies and{" "}
            <strong>{summary?.by_occupation.length ?? "—"}</strong> occupations.
          </p>
          <p style={{ margin: 0, fontSize: 14 }}>
            {topOccupation && (
              <>
                The largest single occupation group is <strong>{topOccupation.name}</strong>
                {topOccupationPct !== null && <> ({topOccupationPct}% of respondents)</>}.
              </>
            )}
          </p>
          <p style={{ margin: 0, fontSize: 14 }}>
            {malePct !== null && (
              <>
                <strong>{malePct}%</strong> of respondents with a known gender are male — worth checking against local demographics
                for under-representation of women in the sample.
              </>
            )}
          </p>
          <p style={{ margin: 0, fontSize: 14 }}>
            {topPriority && (
              <>
                The most-named top priority problem is <strong>{topPriority.name}</strong>
                {topPriorityPct !== null && <> ({topPriorityPct}% of respondents)</>}.
              </>
            )}
          </p>
          {schemeEligibleN > 0 && (
            <p style={{ margin: 0, fontSize: 14 }}>
              Of {schemeEligibleN} respondents asked about a specific livelihood scheme,{" "}
              <strong>{schemeAwarePct !== null ? `${schemeAwarePct}%` : schemeAwareN}</strong> had heard of it before the interview
              — see the scheme-reach section below for the fuller funnel.
            </p>
          )}
          {livelihood && livelihood.earnings.median !== null && (
            <p style={{ margin: 0, fontSize: 14 }}>
              Median reported monthly earnings: <strong>{formatINR(livelihood.earnings.median)}</strong>, from{" "}
              {livelihood.earnings.count} respondents who gave an earnings figure.
            </p>
          )}
        </div>
      </div>

      <h3 style={{ margin: "28px 0 12px" }}>Who works — workforce composition</h3>
      {/* Occupation (10 categories, 2-line-wrapped labels) is naturally far
          taller than everything else in this section -- no CSS alignment
          trick fills that gap cleanly without either stretching a small
          donut's card into mostly dead space, or leaving a short card next
          to a tall one. Grouping similarly-sized content together instead
          of forcing a rigid 2-up grid on everything avoids the problem
          rather than fighting it. */}
      <BarChartCard
        title="Responses by occupation (top 10)"
        data={(summary?.by_occupation ?? []).slice(0, 10)}
        colorIndex={2}
        onBarClick={(d) => toggleFilter("occupation", d.code, d.name)}
        activeCode={filters.occupation}
      />
      <div className="grid cols-2" style={{ marginTop: 20 }}>
        <DonutChartCard
          title="By gender"
          data={toPctData(summary?.by_gender ?? [])}
          colorOffset={0}
          onSliceClick={(d) => toggleFilter("gender", d.code, d.name)}
          activeCode={filters.gender}
        />
        <DonutChartCard
          title="Has a second source of income"
          data={toPctData(summary?.by_second_income ?? [])}
          colorOffset={5}
          onSliceClick={(d) => toggleFilter("has_second_income", d.code, d.name)}
          activeCode={filters.has_second_income}
        />
      </div>
      <div className="grid cols-3" style={{ marginTop: 20 }}>
        <BarChartCard
          title="By age group"
          data={summary?.by_age_group ?? []}
          colorIndex={1}
          onBarClick={(d) => toggleFilter("age_group", d.code, d.name)}
          activeCode={filters.age_group}
        />
        <BarChartCard
          title="By education"
          data={(summary?.by_education ?? []).slice(0, 8)}
          colorIndex={3}
          onBarClick={(d) => toggleFilter("education", d.code, d.name)}
          activeCode={filters.education}
        />
        <BarChartCard
          title="Employment arrangement"
          data={summary?.by_employment_arrangement ?? []}
          colorIndex={4}
          onBarClick={(d) => toggleFilter("employment_arrangement", d.code, d.name)}
          activeCode={filters.employment_arrangement}
        />
      </div>

      {/* Chapter 2 of the Reporting Plan, same title: "having work is not
          the same as having a livelihood" -- earnings, expenses, delayed
          pay and risk/protection together, since the plan's Livelihood
          Security index groups exactly these as one chapter. Work-related
          risks used to sit under "Public priorities" below, which doesn't
          match the plan -- it's a security indicator, not a stated
          priority. */}
      <h3 style={{ margin: "28px 0 4px" }}>How well work pays, and how secure it is</h3>
      <p style={{ margin: "0 0 12px", fontSize: 14, color: "var(--text-secondary)" }}>
        Raw indicators only, from {livelihood?.respondents_with_livelihood_data ?? 0} respondents whose profession module included
        earnings/skills/scheme questions. No combined "Livelihood Security" score is computed — the Reporting Plan defers
        benchmark thresholds and index weighting to after the pilot.
      </p>
      <div className="grid cols-3" style={{ marginBottom: 20 }}>
        <StatTile label="Median monthly earnings" value={livelihood?.earnings.median != null ? formatINR(livelihood.earnings.median) : "—"} />
        <StatTile label="Median monthly expenses" value={livelihood?.expenses.median != null ? formatINR(livelihood.expenses.median) : "—"} tone="neutral" />
        <StatTile label="Avg. months pay was late (12mo)" value={livelihood?.pay_late_months.mean ?? "—"} tone="neutral" />
      </div>
      <div className="grid cols-2">
        <BarChartCard
          title="Median monthly earnings by occupation"
          data={(livelihood?.earnings_by_occupation ?? [])
            // Occupations with only 1-2 earnings responses produce medians
            // that are really just one person's answer (e.g. a single
            // jobseeker's stated expected salary) -- showing them next to
            // occupations with 50+ responses invites reading them as
            // equally reliable. The respondent count is kept in the label
            // instead of hidden, so the small-sample bars that remain are
            // still legible as such.
            .filter((e) => e.count >= MIN_EARNINGS_SAMPLE)
            .slice(0, 10)
            .map((e) => ({ name: `${e.occupation} (n=${e.count})`, code: e.occupation_code, count: e.median ?? 0 }))}
          colorIndex={6}
          valueLabel="Median earnings"
          valueFormatter={formatINR}
          onBarClick={(d) => toggleFilter("occupation", d.code, d.name)}
          activeCode={filters.occupation}
        />
        <BarChartCard title="Work-related risks/incidents reported (top 10)" data={livelihood?.top_risk_incidents ?? []} colorIndex={5} valueLabel="Respondents" />
      </div>

      {/* Chapter 3: "what people can do, and whether anyone recognises it."
          Kept as its own section rather than folded into pay/security --
          skills held is a distinct diagnostic question in the plan, with
          its own Skill Readiness index. */}
      <h3 style={{ margin: "28px 0 12px" }}>What people can do</h3>
      <BarChartCard title="Skills respondents report having (top 10)" data={livelihood?.top_skills_held ?? []} colorIndex={7} valueLabel="Respondents" />

      <h3 style={{ margin: "28px 0 4px" }}>Government scheme reach</h3>
      <p style={{ margin: "0 0 12px", fontSize: 14, color: "var(--text-secondary)" }}>
        Of {livelihood?.scheme_funnel.eligible_modules_n ?? 0} respondents whose module asked about scheme support: only some
        modules ask the full aware → applied → received funnel (6 of 42); the rest ask only what was received, so "received"
        being larger than "aware" reflects that difference in question coverage, not a data error.
      </p>
      <div className="grid cols-3" style={{ marginBottom: 20 }}>
        <StatTile label="Scheme-aware (full-funnel modules)" value={livelihood?.scheme_funnel.aware_n ?? "—"} />
        <StatTile label="Applied for a scheme" value={livelihood?.scheme_funnel.applied_n ?? "—"} tone="neutral" />
        <StatTile label="Received a scheme (any module)" value={livelihood?.scheme_funnel.received_n ?? "—"} tone="neutral" />
      </div>
      <div className="grid cols-2">
        <BarChartCard
          title="General scheme awareness (political section)"
          data={political?.by_scheme_awareness ?? []}
          colorIndex={0}
          onBarClick={(d) => toggleFilter("scheme_awareness", d.code, d.name)}
          activeCode={filters.scheme_awareness}
        />
        <BarChartCard
          title="Healthcare access"
          data={political?.by_healthcare_access ?? []}
          colorIndex={1}
          onBarClick={(d) => toggleFilter("healthcare_access", d.code, d.name)}
          activeCode={filters.healthcare_access}
        />
        <BarChartCard
          title="Schooling access"
          data={political?.by_schooling_access ?? []}
          colorIndex={2}
          onBarClick={(d) => toggleFilter("schooling_access", d.code, d.name)}
          activeCode={filters.schooling_access}
        />
        <BarChartCard
          title="108/104 emergency line usage"
          data={political?.by_emergency_line_usage ?? []}
          colorIndex={3}
          onBarClick={(d) => toggleFilter("emergency_line_usage", d.code, d.name)}
          activeCode={filters.emergency_line_usage}
        />
      </div>

      {/* Chapter 9: what people say vs what the data shows -- risks moved
          to Chapter 2 above, so this section is just stated priorities and
          trust now, matching the plan's own scope for this chapter. */}
      <h3 style={{ margin: "28px 0 12px" }}>Public priorities and trust</h3>
      <div className="grid cols-2">
        <BarChartCard
          title="Top priority problems"
          data={political?.by_priority_problem.slice(0, 8) ?? []}
          colorIndex={4}
          onBarClick={(d) => toggleFilter("top_priority_problem", d.code, d.name)}
          activeCode={filters.top_priority_problem}
        />
        <BarChartCard
          title="Governance trust score (1–5)"
          data={(political?.by_trust_score ?? []).map((t) => ({ name: `Score ${t.score}`, count: t.count }))}
          colorIndex={6}
          valueLabel="Respondents"
        />
      </div>

      <div className="card map-card" style={{ marginTop: 20 }}>
        <h3>Respondent locations ({points.length})</h3>
        <MapView points={points} />
      </div>
    </>
  );
}
