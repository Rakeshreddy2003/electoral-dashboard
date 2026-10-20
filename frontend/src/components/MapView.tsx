import { useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, Marker, TileLayer, Tooltip as LeafletTooltip, useMap } from "react-leaflet";
import L from "leaflet";
import type { Feature, FeatureCollection } from "geojson";
import { seriesColor } from "./charts/palette";
import { TILE_ATTRIBUTION, TILE_MAX_ZOOM, TILE_URL } from "../mapTiles";

export interface MapPoint {
  lat: number;
  lng: number;
  pc_name: string | null;
  ac_name: string | null;
  occupation: string | null;
}

// Fixed PC -> color-slot assignment, shared between boundary polygons and
// respondent points, so a PC's color doesn't depend on point load order.
const PC_COLOR_INDEX: Record<string, number> = {
  Araku: 0,
  Srikakulam: 1,
  Vizianagaram: 2,
  Visakhapatnam: 3,
  Anakapalli: 4,
};

function colorFor(pc: string | null | undefined): string {
  return seriesColor(pc && pc in PC_COLOR_INDEX ? PC_COLOR_INDEX[pc] : 5);
}

function FitBounds({ points, boundaries }: { points: MapPoint[]; boundaries: FeatureCollection | null }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 0) {
      map.fitBounds(L.latLngBounds(points.map((p) => [p.lat, p.lng])), { padding: [24, 24] });
    } else if (boundaries && boundaries.features.length > 0) {
      map.fitBounds(L.geoJSON(boundaries).getBounds(), { padding: [24, 24] });
    }
  }, [points, boundaries, map]);
  return null;
}

interface AcBucket {
  key: string;
  ac_name: string | null;
  pc_name: string | null;
  lat: number;
  lng: number;
  count: number;
  topOccupations: { name: string; count: number }[];
}

// Individual GPS dots were unreadable wherever respondents cluster inside
// the same AC -- a dozen overlapping 5px circles just reads as one smudge,
// with no way to tell 3 responses from 30. Aggregating to one bubble per
// AC (centroid of its points, sized by response count, with the count
// printed inside it) answers "where are our responses coming from" far
// better than the raw scatter did, at the same geographic granularity the
// rest of the app already uses (AC, not exact GPS).
function bucketByAc(points: MapPoint[]): AcBucket[] {
  const buckets = new Map<string, { pc_name: string | null; ac_name: string | null; lat: number; lng: number; n: number; occ: Map<string, number> }>();
  for (const p of points) {
    const key = p.ac_name ?? `unmapped:${p.lat.toFixed(2)},${p.lng.toFixed(2)}`;
    let b = buckets.get(key);
    if (!b) {
      b = { pc_name: p.pc_name, ac_name: p.ac_name, lat: 0, lng: 0, n: 0, occ: new Map() };
      buckets.set(key, b);
    }
    b.lat += p.lat;
    b.lng += p.lng;
    b.n += 1;
    if (p.occupation) b.occ.set(p.occupation, (b.occ.get(p.occupation) ?? 0) + 1);
  }
  return [...buckets.entries()].map(([key, b]) => ({
    key,
    ac_name: b.ac_name,
    pc_name: b.pc_name,
    lat: b.lat / b.n,
    lng: b.lng / b.n,
    count: b.n,
    topOccupations: [...b.occ.entries()]
      .sort((a, z) => z[1] - a[1])
      .slice(0, 3)
      .map(([name, count]) => ({ name, count })),
  }));
}

function bubbleIcon(count: number, color: string): L.DivIcon {
  // sqrt-scaled so bubble AREA (not radius) is proportional to count --
  // a linear radius scale makes a 10x response count look ~10x wider,
  // which reads as a far bigger difference than it should.
  const size = Math.round(24 + Math.sqrt(count) * 6);
  return L.divIcon({
    className: "resp-bubble",
    html: `<div style="width:${size}px;height:${size}px;background:${color};">${count}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export default function MapView({ points }: { points: MapPoint[] }) {
  const [boundaries, setBoundaries] = useState<FeatureCollection | null>(null);

  useEffect(() => {
    fetch("/ac_boundaries.geojson")
      .then((res) => (res.ok ? res.json() : null))
      .then(setBoundaries)
      .catch(() => setBoundaries(null));
  }, []);

  const buckets = useMemo(() => bucketByAc(points), [points]);

  // Default center: North Andhra coastal belt, before boundaries/points load / fitBounds runs.
  const defaultCenter: [number, number] = [18.0, 83.3];

  return (
    <MapContainer
      center={defaultCenter}
      zoom={7}
      zoomControl={false}
      scrollWheelZoom={false}
      doubleClickZoom={false}
      boxZoom={false}
      touchZoom={false}
    >
      <TileLayer attribution={TILE_ATTRIBUTION} url={TILE_URL} maxZoom={TILE_MAX_ZOOM} />
      <FitBounds points={points} boundaries={boundaries} />
      {boundaries && (
        <GeoJSON
          data={boundaries}
          style={(feature?: Feature) => {
            const pc = feature?.properties?.pc_name as string | undefined;
            return { color: colorFor(pc), weight: 1.5, fillColor: colorFor(pc), fillOpacity: 0.08 };
          }}
          onEachFeature={(feature, layer) => {
            const { ac_name, pc_name } = feature.properties as { ac_name: string; pc_name: string };
            layer.bindTooltip(`${ac_name} (${pc_name})`);
          }}
        />
      )}
      {buckets.map((b) => (
        <Marker key={b.key} position={[b.lat, b.lng]} icon={bubbleIcon(b.count, colorFor(b.pc_name))}>
          <LeafletTooltip>
            <div>
              <strong>{b.ac_name || "Unmapped location"}</strong>
              {b.pc_name && ` (${b.pc_name})`}
              <br />
              {b.count} response{b.count === 1 ? "" : "s"}
              {b.topOccupations.length > 0 && (
                <>
                  <br />
                  Top: {b.topOccupations.map((o) => `${o.name} (${o.count})`).join(", ")}
                </>
              )}
            </div>
          </LeafletTooltip>
        </Marker>
      ))}
    </MapContainer>
  );
}
