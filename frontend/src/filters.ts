import { useOutletContext } from "react-router-dom";

// The PC/AC filter picked in the header is shared across all three pages
// (via the route Outlet's context) rather than kept as separate per-page
// state, so picking a constituency once stays selected while clicking
// through Retrospective Data / Form Responses / Influencers -- the point
// for a client walkthrough, where the presenter picks a constituency and
// narrates all three pages against it.
export interface Ac {
  ac_name: string;
  pc_name: string | null;
}

export interface GlobalFilters {
  pcName: string;
  acName: string;
  setPcName: (pc: string) => void;
  setAcName: (ac: string) => void;
  acs: Ac[];
}

export function useGlobalFilters() {
  return useOutletContext<GlobalFilters>();
}
