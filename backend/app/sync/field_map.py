"""
Maps ODK Central OData field paths (dot-notation for groups) to SurveyResponse
columns.

Verified against a real synced submission (2026-10-19, 251 submissions from
the live ODK Central instance) -- these are confirmed field names and value
formats, not guesses. See docs/reference/North_Andhra_Livelihoods_Survey_ODK.xlsx
for the full question list if a field is ever renamed there.

Notes on value formats, confirmed from real data:
  - `interview_geopoint` is a GeoJSON Point: {"coordinates": [lon, lat, alt],
    "properties": {"accuracy": ...}} -- longitude first, per GeoJSON order.
  - `pol_trust_satisfaction` and other 1-5 scale questions are select_ones
    with choice names "1".."5" (strings), not integer-type fields -- cast
    with int() in odk_sync.py, don't assign the string directly.
  - The form has no mandal/village question -- location is captured as
    PC/AC choice + GPS point only. SurveyResponse.mandal/village stay null.
  - Profession-module answers live in a per-occupation group named
    grp_prof_<main_occupation> (e.g. grp_prof_agriculture, grp_prof_students)
    -- the group name always matches the occupation choice value exactly, so
    this is looked up dynamically in odk_sync.py rather than listed here.
"""

FIELD_MAP = {
    "parliamentary_constituency": "grp_profile.pc_constituency",
    "assembly_constituency": "grp_profile.ac_constituency",
    "age_group": "grp_profile.age_group",
    "gender": "grp_profile.gender",
    "marital_status": "grp_profile.marital_status",
    "education": "grp_profile.education",
    "occupation": "grp_profile.main_occupation",
    "employment_arrangement": "grp_profile.work_type",
    "household_size": "grp_profile.household_size",
    "monthly_expenditure": "grp_profile.household_expenditure",
    "has_second_income": "grp_profile.has_second_income",
    "second_occupation": "grp_profile.second_occupation",
    "top_priority_problem": "grp_political.pol_priority_problem",
    "trust_score": "grp_political.pol_trust_satisfaction",
    "scheme_awareness": "grp_political.pol_scheme_awareness",
    "healthcare_access": "grp_political.hc_access",
    "schooling_access": "grp_political.sch_access",
    "emergency_line_usage": "grp_political.emergency_108_104",
    "respondent_category": "grp_political.pol_respondent_category",
    "contact_name": "grp_political.pol_respondent_category_name",
    "contact_phone_1": "grp_political.pol_respondent_category_contact_primary",
    "contact_phone_2": "grp_political.pol_respondent_category_contact_secondary",
}

# grp_profile.pc_constituency / ac_constituency store the XLSForm's lowercase
# choice slugs, not the display name -- every filter elsewhere (dropdowns,
# /retrospective endpoints, constituencies_config.PC_TO_ACS) uses the Title
# Case name, so these must be translated at sync time or PC/AC filtering on
# the Responses page would silently match nothing. Source: the `pc`/`ac`
# choice lists in questionnaire/scripts/build_xlsform_v2.py (confirmed
# in dashboard/docs/reference/build_xlsform_v2.py), with the same 3 ECI
# spelling corrections already applied in constituencies_config.py.
PC_SLUG_TO_NAME = {
    "visakhapatnam": "Visakhapatnam",
    "anakapalli": "Anakapalli",
    "srikakulam": "Srikakulam",
    "vizianagaram": "Vizianagaram",
    "araku": "Araku",
}

AC_SLUG_TO_NAME = {
    "gajuwaka": "Gajuwaka",
    "bhimli": "Bhimili",
    "srungavarapukota": "Srungavarapukota",
    "visakhapatnam_south": "Visakhapatnam South",
    "visakhapatnam_north": "Visakhapatnam North",
    "visakhapatnam_east": "Visakhapatnam East",
    "visakhapatnam_west": "Visakhapatnam West",
    "anakapalle": "Anakapalle",
    "madugula": "Madugula",
    "narsipatnam": "Narsipatnam",
    "chodavaram": "Chodavaram",
    "payakaraopet": "Payakaraopet",
    "pendurthi": "Pendurthi",
    "elamanchili": "Yelamanchili",
    "narasannapeta": "Narasannapeta",
    "srikakulam_ac": "Srikakulam",
    "tekkali": "Tekkali",
    "pathapatnam": "Pathapatnam",
    "ichchapuram": "Ichchapuram",
    "palasa": "Palasa",
    "amadalavalasa": "Amadalavalasa",
    "cheepurupalle": "Cheepurupalle",
    "bobbili": "Bobbili",
    "gajapathinagaram": "Gajapathinagaram",
    "etcherla": "Etcherla",
    "nellimarla": "Nellimarla",
    "rajam": "Rajam",
    "vizianagaram_ac": "Vizianagaram",
    "rampachodavaram": "Rampachodavaram",
    "paderu": "Paderu",
    "kurupam": "Kurupam",
    "araku_valley": "Araku Valley",
    "palakonda": "Palakonda",
    "salur": "Salur",
    "parvathipuram": "Parvathipuram",
}

# grp_political.pol_respondent_category's real choice values (confirmed from
# the XLSForm's choices sheet) -- translated to the Title Case labels the
# API/frontend filter on (routes_influencers.py, Influencers.tsx CATEGORIES),
# since the raw values are lowercase slugs, not the display label.
RESPONDENT_CATEGORY_LABELS = {
    "neutral_influencer": "Neutral Influencer",
    "volunteer_army": "Volunteer Army",
    "not_applicable": "Not applicable",
}


def get_nested(data: dict, dotted_path: str):
    node = data
    for part in dotted_path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node
