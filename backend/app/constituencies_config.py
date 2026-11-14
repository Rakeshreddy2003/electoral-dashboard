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



# The real ECI assembly-constituency number for each AC above (not a
# dashboard-internal id) -- read off data/retro/acs.csv's own `ac_no` column
# (see backend/etl/load_eci_data.py), keyed by this file's canonical AC name.
# This is the numeric join key between survey data (SurveyResponse.ac_no,
# backfilled from this dict via assembly_constituency -> AC_NO) and
# retrospective ECI data (EciResult.constituency_no, loaded straight from the
# source CSV) -- previously the two datasets were only ever joined by
# matching name strings, with no shared numeric id and no table that
# verified the two name sets actually agreed. Verified 35/35 exact name
# match against data/retro/acs.csv before adding this (2026-11-12); note
# Rampachodavaram's 53 is correct, not a typo -- it's a non-contiguous AC
# number in the real ECI sequence, not a dashboard artifact.
AC_NO: dict[str, int] = {
    "Rampachodavaram": 53,
    "Paderu": 29,
    "Kurupam": 11,
    "Araku Valley": 28,
    "Palakonda": 10,
    "Salur": 13,
    "Parvathipuram": 12,
    "Narasannapeta": 8,
    "Srikakulam": 5,
    "Tekkali": 3,
    "Pathapatnam": 4,
    "Ichchapuram": 1,
    "Palasa": 2,
    "Amadalavalasa": 6,
    "Cheepurupalle": 15,
    "Bobbili": 14,
    "Gajapathinagaram": 16,
    "Etcherla": 7,
    "Nellimarla": 17,
    "Rajam": 9,
    "Vizianagaram": 18,
    "Gajuwaka": 25,
    "Bhimili": 20,
    "Srungavarapukota": 19,
    "Visakhapatnam South": 22,
    "Visakhapatnam North": 23,
    "Visakhapatnam East": 21,
    "Visakhapatnam West": 24,
    "Anakapalle": 30,
    "Madugula": 27,
    "Narsipatnam": 34,
    "Chodavaram": 26,
    "Payakaraopet": 33,
    "Pendurthi": 31,
    "Yelamanchili": 32,
}


def is_configured() -> bool:
    return all(len(acs) > 0 for acs in PC_TO_ACS.values())


def ac_to_pc(ac_name: str) -> str | None:
    for pc, acs in PC_TO_ACS.items():
        if ac_name in acs:
            return pc
    return None


def ac_to_no(ac_name: str | None) -> int | None:
    if ac_name is None:
        return None
    return AC_NO.get(ac_name)
