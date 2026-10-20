// Basemap tile source, shared by both map components.
//
// Tried, in order, and actually verified by downloading and looking at a
// real tile (not just checking the HTTP status -- a 200 with a watermark
// image looks identical to a working tile at the status-code level):
//   - OSM's own tile.openstreetmap.org: blocks this kind of app embedding
//     without prior registration (osm.wiki/Blocked) -- confirmed broken.
//   - CARTO's basemaps.cartocdn.com: now requires an API key; every tile
//     came back as a 200 OK PNG, but the image itself is a gray
//     "API KEY REQUIRED" placeholder, not a map -- confirmed broken by
//     actually opening the downloaded tile.
//   - Esri's World_Light_Gray_Base, via services.arcgisonline.com: free, no
//     key, confirmed by downloading a tile and viewing it -- a real,
//     clean, light basemap matching this dashboard's look. In use below.
//
// Esri's tile path is {z}/{y}/{x} (row before column), not the usual
// {z}/{x}/{y} -- Leaflet just substitutes whichever named tokens appear in
// the URL template, so writing them in this order is enough; no extra
// config needed.
export const TILE_URL = "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}";
export const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.esri.com">Esri</a> &mdash; Esri, HERE, Garmin, FAO, NOAA, USGS';
export const TILE_MAX_ZOOM = 16; // Esri's World_Light_Gray_Base caps out here; deeper zoom reuses the last level
