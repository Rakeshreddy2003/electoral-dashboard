import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, FeatureCollection } from "geojson";
import L from "leaflet";
import { api } from "../../api/client";
import { partyColor } from "./partyColors";
import { TILE_ATTRIBUTION, TILE_MAX_ZOOM, TILE_URL } from "../../mapTiles";

interface AcOverview {
  ac_name: string;
  pc_name: string;
  latest_year: number;
  winner_name: string;
  party: string;
  vote_share_percentage: number;
  margin_percentage: number;
  turnout_percentage: number;
}

interface PcOverview {
  pc_name: string;
  latest_year: number;
  winner_name: string;
  party: string;
  vote_share_percentage: number;
  turnout_percentage: number;
}

function FitToFeatures({ data }: { data: FeatureCollection | null }) {
  const map = useMap();
  useEffect(() => {
    if (!data || data.features.length === 0) return;
    map.fitBounds(L.geoJSON(data).getBounds(), { padding: [20, 20] });
  }, [data, map]);
  return null;
}

function mergeFeatureCollections(...collections: (FeatureCollection | null)[]): FeatureCollection | null {
  const features = collections.flatMap((c) => c?.features ?? []);
  return features.length ? { type: "FeatureCollection", features } : null;
}

export default function RetrospectiveMap({
  selectedPc,
  onSelectPc,
  onSelectAc,
}: {
  selectedPc: string | null;
  onSelectPc: (pc: string) => void;
  onSelectAc: (ac: string) => void;
}) {
  const [pcBoundaries, setPcBoundaries] = useState<FeatureCollection | null>(null);
  const [acBoundaries, setAcBoundaries] = useState<FeatureCollection | null>(null);
  // The rest of Andhra Pradesh's ~140 other ACs -- pure background context so
  // the 5 surveyed PCs read as part of the real state map, not a shape
  // floating in empty space. Rendered non-interactive and never colored by
  // party; it's geography, not data this dashboard has an opinion on.
  const [apContext, setApContext] = useState<FeatureCollection | null>(null);
  const [overview, setOverview] = useState<{ acs: AcOverview[]; pcs: PcOverview[] } | null>(null);

  useEffect(() => {
    fetch("/pc_boundaries.geojson").then((r) => r.json()).then(setPcBoundaries);
    fetch("/ac_boundaries.geojson").then((r) => r.json()).then(setAcBoundaries);
    fetch("/ap_context_boundaries.geojson").then((r) => r.json()).then(setApContext);
    api.get("/retrospective/ap-overview").then((res) => setOverview(res.data));
  }, []);

  const acOverviewByName = new Map((overview?.acs ?? []).map((a) => [a.ac_name, a]));
  const pcOverviewByName = new Map((overview?.pcs ?? []).map((p) => [p.pc_name, p]));

  const acsForSelectedPc: FeatureCollection | null =
    selectedPc && acBoundaries
      ? { type: "FeatureCollection", features: acBoundaries.features.filter((f) => f.properties?.pc_name === selectedPc) }
      : null;

  const displayData = selectedPc ? acsForSelectedPc : pcBoundaries;
  // At the top-level (no PC picked) the map should fit the WHOLE state, so
  // North Andhra reads as the corner of AP it actually is rather than
  // filling the frame as if it were the entire map. Once a PC is picked we
  // go back to fitting tightly to just its 7 ACs -- the context layer is
  // still drawn underneath then, it's just mostly off-screen, which is fine.
  const boundsTarget = selectedPc ? acsForSelectedPc : mergeFeatureCollections(pcBoundaries, apContext);

  function tooltipHtml(isAc: boolean, name: string, pcName?: string): string {
    if (isAc) {
      const o = acOverviewByName.get(name);
      if (!o) return `<strong>${name}</strong>`;
      return `<strong>${name}</strong> (${o.pc_name})<br/>${o.latest_year} winner: ${o.winner_name} (${o.party})<br/>Vote share: ${o.vote_share_percentage?.toFixed(1)}% &middot; Margin: ${o.margin_percentage?.toFixed(1)}%<br/>Turnout: ${o.turnout_percentage?.toFixed(1)}%<br/><em>Click for full detail</em>`;
    }
    const o = pcOverviewByName.get(name);
    if (!o) return `<strong>${name}</strong>`;
    return `<strong>${name} (Lok Sabha)</strong><br/>${o.latest_year} winner: ${o.winner_name} (${o.party})<br/>Vote share: ${o.vote_share_percentage?.toFixed(1)}% &middot; Turnout: ${o.turnout_percentage?.toFixed(1)}%<br/><em>Click to zoom into this constituency</em>`;
  }

  return (
    <div>
      {selectedPc && (
        <button className="hero-back-btn" onClick={() => onSelectPc("")}>
          ← Back to all 5 constituencies
        </button>
      )}
      <MapContainer
        center={[18.0, 83.3]}
        zoom={7}
        style={{ height: 480 }}
        zoomControl={false}
        scrollWheelZoom={false}
        doubleClickZoom={false}
        boxZoom={false}
        touchZoom={false}
      >
        <TileLayer attribution={TILE_ATTRIBUTION} url={TILE_URL} maxZoom={TILE_MAX_ZOOM} />
        <FitToFeatures data={boundsTarget} />
        {apContext && (
          <GeoJSON
            key="ap-context"
            data={apContext}
            interactive={false}
            // Needs real contrast against the Esri light-gray basemap, not
            // the page's own --border/--surface-sunken tokens -- those are
            // tuned for a light page background and were nearly invisible
            // here, which read as "the rest of the state is missing" when
            // the ~140 other ACs were actually rendering all along.
            style={{ color: "#9aa0b4", weight: 1, fillColor: "#c7cce0", fillOpacity: 0.55 }}
          />
        )}
        {displayData && (
          <GeoJSON
            key={selectedPc || "all"}
            data={displayData}
            // Fill bumped from 0.35/0.6 to 0.5/0.78 -- the thin, washed-out
            // outlines read fine against the old stark-white page but got
            // lost against the new softer pastel background. A stronger
            // fill plus a heavier border gives the constituencies real
            // visual presence instead of relying on the page behind them
            // for contrast.
            style={(feature?: Feature) => {
              const pcName = (feature?.properties?.pc_name as string) || (feature?.properties?.ac_name as string);
              return {
                color: partyColor(selectedPc ? acOverviewByName.get(feature?.properties?.ac_name)?.party : pcOverviewByName.get(pcName)?.party),
                weight: selectedPc ? 2.5 : 3,
                fillOpacity: 0.5,
              };
            }}
            onEachFeature={(feature, layer) => {
              const isAc = !!selectedPc;
              const name = isAc ? feature.properties.ac_name : feature.properties.pc_name;
              layer.bindTooltip(tooltipHtml(isAc, name), { sticky: true });
              layer.on("click", () => {
                if (isAc) onSelectAc(name);
                else onSelectPc(name);
              });
              layer.on("mouseover", () => (layer as L.Path).setStyle({ fillOpacity: 0.78 }));
              layer.on("mouseout", () => (layer as L.Path).setStyle({ fillOpacity: 0.5 }));
            }}
          />
        )}
      </MapContainer>
      <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
        {selectedPc
          ? "Hover an assembly segment for its latest result; click for full detail. Color shows the winning party."
          : "Hover a constituency for its latest Lok Sabha result; click to zoom in and see its 7 assembly segments."}
      </p>
    </div>
  );
}
