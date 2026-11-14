import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, FeatureCollection } from "geojson";
import L from "leaflet";
import { api } from "../../api/client";
import { partyColor } from "./partyColors";
import { TILE_ATTRIBUTION, TILE_LABELS_URL, TILE_MAX_ZOOM, TILE_URL } from "../../mapTiles";

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

type View = "north" | "state";

function FitToFeatures({ data, padding }: { data: FeatureCollection | null; padding: number }) {
  const map = useMap();
  useEffect(() => {
    if (!data || data.features.length === 0) return;
    map.fitBounds(L.geoJSON(data).getBounds(), { padding: [padding, padding] });
  }, [data, map, padding]);
  return null;
}

// Name tags sit on the shapes permanently, so nobody has to hover to learn
// which constituency is which.
function NameLabels({ data, nameKey }: { data: FeatureCollection | null; nameKey: "pc_name" | "ac_name" }) {
  const map = useMap();
  useEffect(() => {
    if (!data) return;
    const tags = data.features.map((f) => {
      const center = L.geoJSON(f).getBounds().getCenter();
      return L.tooltip({ permanent: true, direction: "center", className: "map-label", interactive: false })
        .setLatLng(center)
        .setContent(String(f.properties?.[nameKey] ?? ""))
        .addTo(map);
    });
    return () => {
      tags.forEach((t) => t.remove());
    };
  }, [data, map, nameKey]);
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
  const [apContext, setApContext] = useState<FeatureCollection | null>(null);
  const [overview, setOverview] = useState<{ acs: AcOverview[]; pcs: PcOverview[] } | null>(null);
  const [view, setView] = useState<View>("north");

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
  // "North Andhra" fits tightly to the surveyed area so shapes are big
  // enough to read; "Whole state" zooms out to show where it sits in AP.
  const boundsTarget = selectedPc ? acsForSelectedPc : view === "state" ? mergeFeatureCollections(pcBoundaries, apContext) : pcBoundaries;

  const partiesShown = [...new Set((selectedPc ? acsForSelectedPc : pcBoundaries)?.features.map((f) => {
    const name = f.properties?.[selectedPc ? "ac_name" : "pc_name"];
    return (selectedPc ? acOverviewByName.get(name)?.party : pcOverviewByName.get(name)?.party) ?? "";
  }).filter(Boolean))];

  function tooltipHtml(isAc: boolean, name: string): string {
    if (isAc) {
      const o = acOverviewByName.get(name);
      if (!o) return `<strong>${name}</strong>`;
      return `<strong>${name}</strong> (${o.pc_name})<br/>${o.latest_year} winner: ${o.winner_name} (${o.party})<br/>Vote share ${o.vote_share_percentage?.toFixed(1)}%, won by ${o.margin_percentage?.toFixed(1)}%<br/>Turnout ${o.turnout_percentage?.toFixed(1)}%<br/><em>Select for full detail</em>`;
    }
    const o = pcOverviewByName.get(name);
    if (!o) return `<strong>${name}</strong>`;
    return `<strong>${name} (Lok Sabha)</strong><br/>${o.latest_year} winner: ${o.winner_name} (${o.party})<br/>Vote share ${o.vote_share_percentage?.toFixed(1)}%, turnout ${o.turnout_percentage?.toFixed(1)}%<br/><em>Select to see its 7 assembly seats</em>`;
  }

  return (
    <div>
      <div className="map-toolbar">
        {selectedPc ? (
          <button type="button" onClick={() => onSelectPc("")}>
            ← All 5 parliamentary constituencies
          </button>
        ) : (
          <>
            <button type="button" aria-pressed={view === "north"} onClick={() => setView("north")}>
              North Andhra
            </button>
            <button type="button" aria-pressed={view === "state"} onClick={() => setView("state")}>
              Whole state
            </button>
          </>
        )}
      </div>
      {partiesShown.length > 0 && (
        <div className="map-legend" aria-label="Map colours show the winning party">
          <span>Colour shows the {selectedPc ? "assembly" : "Lok Sabha"} winner:</span>
          {partiesShown.map((p) => (
            <span key={p}>
              <i className="seat-swatch" style={{ background: partyColor(p) }} />
              {p}
            </span>
          ))}
        </div>
      )}
      <MapContainer
        center={[18.0, 83.3]}
        zoom={8}
        style={{ height: 540, marginTop: 12 }}
        zoomControl
        zoomSnap={0.25}
        zoomDelta={0.5}
        scrollWheelZoom={false}
        doubleClickZoom={false}
        boxZoom={false}
      >
        <TileLayer attribution={TILE_ATTRIBUTION} url={TILE_URL} maxZoom={TILE_MAX_ZOOM} />
        <FitToFeatures data={boundsTarget} padding={view === "state" && !selectedPc ? 20 : 36} />
        {apContext && (
          <GeoJSON
            key="ap-context"
            data={apContext}
            interactive={false}
            // Explicit colours with real contrast against the light Esri
            // basemap; the page's own border tokens were nearly invisible here.
            style={{ color: "#7f87a3", weight: 1, fillColor: "#b8bfd6", fillOpacity: 0.55 }}
          />
        )}
        {displayData && (
          <GeoJSON
            key={selectedPc || "all"}
            data={displayData}
            style={(feature?: Feature) => {
              const pcName = (feature?.properties?.pc_name as string) || (feature?.properties?.ac_name as string);
              return {
                color: partyColor(selectedPc ? acOverviewByName.get(feature?.properties?.ac_name)?.party : pcOverviewByName.get(pcName)?.party),
                weight: 3,
                fillOpacity: 0.62,
              };
            }}
            onEachFeature={(feature, layer) => {
              const isAc = !!selectedPc;
              const name = isAc ? feature.properties.ac_name : feature.properties.pc_name;
              layer.bindTooltip(tooltipHtml(isAc, name), { sticky: true, className: "map-hover" });
              layer.on("click", () => {
                if (isAc) onSelectAc(name);
                else onSelectPc(name);
              });
              layer.on("mouseover", () => (layer as L.Path).setStyle({ fillOpacity: 0.85 }));
              layer.on("mouseout", () => (layer as L.Path).setStyle({ fillOpacity: 0.62 }));
            }}
          />
        )}
        {/* Reference tiles (town and district names) sit above the shapes. */}
        <TileLayer url={TILE_LABELS_URL} maxZoom={TILE_MAX_ZOOM} pane="shadowPane" />
        <NameLabels data={displayData} nameKey={selectedPc ? "ac_name" : "pc_name"} />
      </MapContainer>
      <p>
        {selectedPc
          ? "Point at a seat for its latest result, or select it to open that constituency."
          : "Point at a constituency for its latest Lok Sabha result, or select it to see its assembly seats."}
      </p>
    </div>
  );
}
