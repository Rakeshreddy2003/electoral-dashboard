"""
Mapping of the 5 parliamentary constituencies (PCs) this survey covers to their
35 assembly constituencies (ACs), for grouping ECI historical results on the
Retrospective page.

Cross-verified from two independent sources, both agreeing 35/35:
  1. The `ac_list` choice table in docs/reference/build_xlsform_v2.py (the
     XLSForm build script's own PC/AC choice list, authoritative for this
     survey -- the live version lives in the separate questionnaire/
     project).
  2. The official `ac_master.csv` (pcName/asmblyName columns) from the
     andhra_pradesh_retro MATData export, via data/retro/acs.csv +
     data/retro/pcs.csv (see backend/etl/load_eci_data.py).

Three ACs needed their ECI/MATData spelling substituted for the XLSForm's
internal code/label:
  - XLSForm "bhimli"        -> official "Bhimili"
  - XLSForm "araku_valley"  -> official "Araku Valley" (capitalization)
  - XLSForm "elamanchili"   -> official "Yelamanchili"
One PC name also needed substituting: MATData's ac_master.csv spells it
"Anakapalle", not "Anakapalli" -- pcs.csv (used for the PC/GE Lok Sabha
results) already uses "Anakapalli", matching this file's canonical key.
"""

PC_TO_ACS: dict[str, list[str]] = {
    "Araku": [
        "Rampachodavaram",
        "Paderu",
        "Kurupam",
        "Araku Valley",
        "Palakonda",
        "Salur",
        "Parvathipuram",
    ],
    "Srikakulam": [
        "Narasannapeta",
        "Srikakulam",
        "Tekkali",
        "Pathapatnam",
        "Ichchapuram",
        "Palasa",
        "Amadalavalasa",
    ],
    "Vizianagaram": [
        "Cheepurupalle",
        "Bobbili",
        "Gajapathinagaram",
        "Etcherla",
        "Nellimarla",
        "Rajam",
        "Vizianagaram",
    ],
    "Visakhapatnam": [
        "Gajuwaka",
        "Bhimili",
        "Srungavarapukota",
        "Visakhapatnam South",
        "Visakhapatnam North",
        "Visakhapatnam East",
        "Visakhapatnam West",
    ],
    "Anakapalli": [
        "Anakapalle",
        "Madugula",
        "Narsipatnam",
        "Chodavaram",
        "Payakaraopet",
        "Pendurthi",
        "Yelamanchili",
    ],
}


def is_configured() -> bool:
    return all(len(acs) > 0 for acs in PC_TO_ACS.values())


def ac_to_pc(ac_name: str) -> str | None:
    for pc, acs in PC_TO_ACS.items():
        if ac_name in acs:
            return pc
    return None
