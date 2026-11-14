// Party brand colors, taken from the user's canonical national/state party
// color map (same source used across their other election dashboards, e.g.
// webapp/tn/report_tn.py) so this dashboard matches the rest of their work.
// A few parties that appear in this dataset but not in that source map
// (PRAP, BAP, IND) are filled in from unused entries of the same map to
// stay visually consistent and distinct.
const PARTY_COLORS: Record<string, string> = {
  TDP: "#FCEE23",
  YSRCP: "#1569C7",
  BJP: "#FF9933",
  INC: "#19AAED",
  BSP: "#22409A",
  CPM: "#FF1D15", // CPI(M)
  JnP: "#DA2824", // Jana Sena Party (JSP) -- the dataset's party_code for this party is "JnP", not "JSP"
  PRAP: "#DB7093", // from NPP
  BAP: "#008000", // from RJD/PPA
  IND: "#696969", // from "Others"
};

const FALLBACK_COLOR = "#8a8a85";

export function partyColor(party: string | null | undefined): string {
  if (!party) return FALLBACK_COLOR;
  return PARTY_COLORS[party] ?? FALLBACK_COLOR;
}

function luminance(hex: string): number {
  const n = parseInt(hex.slice(1), 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// White text is illegible on the light party colors (TDP yellow, BJP
// saffron, INC sky blue), so tag text flips to ink on those.
export function partyTagStyle(party: string | null | undefined): { background: string; color: string } {
  const background = partyColor(party);
  return { background, color: luminance(background) > 0.3 ? "#1c1f26" : "#ffffff" };
}
