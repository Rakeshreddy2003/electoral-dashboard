import { useEffect, useState } from "react";
import { api } from "../../api/client";
import DonutChartCard from "../charts/DonutChartCard";
import StatTile from "../charts/StatTile";

interface Breakdown {
  name: string;
  count: number;
  pct: number;
}

interface Demographics {
  secretariat_count: number;
  population: number;
  households: number;
  pct_bpl_proxy_hh: number | null;
  caste_breakdown: Breakdown[];
  religion_breakdown: Breakdown[];
}

const CASTE_LABELS: Record<string, string> = {
  Other_BC: "Other BC",
  Kapu_BC: "Kapu (BC)",
  Muslim_BC: "Muslim (BC)",
  OC_Forward: "OC / Forward",
  Kamma: "Kamma",
  Reddy: "Reddy",
  SC: "SC",
  ST: "ST",
  Unknown: "Unknown",
};

export default function DemographicsCard({ acName, pcName }: { acName?: string; pcName?: string }) {
  const [data, setData] = useState<Demographics | null>(null);

  useEffect(() => {
    // No ac/pc -- fetch the region-wide aggregate (all 5 PCs) rather than
    // skipping the request, so this card also has something to show on
    // the unscoped overview, not only once a PC or AC is picked.
    const params = acName ? { ac_name: acName } : pcName ? { pc_name: pcName } : {};
    api.get("/retrospective/demographics", { params }).then((res) => setData(res.data));
  }, [acName, pcName]);

  if (!data) return null;

  return (
    <div style={{ marginBottom: 20 }}>
      <h3 style={{ margin: "0 0 4px" }}>Socio-economic baseline ({acName || pcName || "all 5 PCs"})</h3>
      <p style={{ margin: "0 0 12px", fontSize: 14, color: "var(--text-secondary)" }}>
        Pre-survey baseline from {data.secretariat_count} secretariats, not survey findings. The BPL proxy predates AP's 2024
        change of government and is tied to welfare schemes that may since have been renamed or discontinued — treat it as a
        baseline-era figure to compare the survey against, not a current one.
      </p>
      <div className="grid cols-3" style={{ marginBottom: 20 }}>
        <StatTile label="Population" value={data.population.toLocaleString()} tone="neutral" />
        <StatTile label="Households" value={data.households.toLocaleString()} tone="neutral" />
        <StatTile label="BPL-proxy households" value={data.pct_bpl_proxy_hh != null ? `${data.pct_bpl_proxy_hh}%` : "—"} />
      </div>
      <div className="grid cols-2">
        <DonutChartCard
          title="Caste composition"
          data={data.caste_breakdown.map((b) => ({ name: CASTE_LABELS[b.name] || b.name, pct: b.pct }))}
          colorOffset={1}
        />
        <DonutChartCard
          title="Religion composition"
          data={data.religion_breakdown.map((b) => ({ name: b.name, pct: b.pct }))}
          colorOffset={3}
        />
      </div>
    </div>
  );
}
