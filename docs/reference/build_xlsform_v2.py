# -*- coding: utf-8 -*-
"""
XLSForm v2: Demographic + Common (Sec.1) -> Profession routing (Sec.2, Weavers sample)
-> Political (Sec.3, common to all).
Design rules applied per user feedback:
  - No "Q1./Q2." numbering in labels anywhere (source docs' own numbering collides/duplicates,
    e.g. Political doc reuses "5." twice -- any fixed number shown to a respondent who may skip
    conditional questions would be actively misleading). Kobo/ODK Collect already shows a
    built-in "X of Y" progress indicator. Internal `name` codes carry stable mnemonic
    references for analysts instead (e.g. wv_loom_type, pol_trust_village).
  - Section headers use plain descriptive titles, no decorative letter prefixes (A./B./ఎ./బి.)
    since Telugu letters like "ఎ" are not natural equivalents of Latin "A" and read oddly.
  - Pure standard XLSForm (select_one/select_multiple/integer/decimal/text/note/begin group/
    end group, relevant/constraint/choice_filter/required) -- no Kobo-only extensions
    (no search(), no dynamic pulldata) so the same file imports cleanly into KoboToolbox
    AND a self-hosted ODK Central/Collect stack via pyxform.
"""
import openpyxl
from openpyxl import Workbook

EN = "label::English (en)"
TE = "label::Telugu (te)"
HEN = "hint::English (en)"
HTE = "hint::Telugu (te)"

SURVEY_COLS = ["type", "name", EN, TE, HEN, HTE, "required", "relevant",
               "constraint", "constraint_message::English (en)", "choice_filter", "appearance"]
CHOICE_COLS = ["list_name", "name", EN, TE, "pc_filter", "occ_filter"]

wb = Workbook()
ws = wb.active
ws.title = "survey"
ws.append(SURVEY_COLS)

def row(type_, name, en, te, hen="", hte="", required="", relevant="", constraint="",
        cmsg="", choice_filter="", appearance=""):
    ws.append([type_, name, en, te, hen, hte, required, relevant, constraint, cmsg, choice_filter, appearance])

def group(name, en, te, relevant=""):
    row("begin group", name, en, te, relevant=relevant)

def end_group():
    ws.append(["end group", "", "", "", "", "", "", "", "", "", "", ""])

def note(name, en, te, relevant=""):
    row("note", name, en, te, relevant=relevant)

# =====================================================================
# SECTION 1: PROFILE & ROUTING (hard cap: 5-10 questions per the client's
# total-interview-length directive -- identity + occupation routing +
# ONE shared livelihood metric; everything else now lives in the
# profession module instead, which has more room under its own budget).
# =====================================================================
row("note", "sec1_title", "SECTION 1: Profile",
    "విభాగం 1: వ్యక్తిగత వివరాలు")

group("grp_profile", "Profile", "వ్యక్తిగత వివరాలు")

row("select_one pc", "pc_constituency",
    "Which Parliamentary Constituency (Lok Sabha seat) do you live in?",
    "మీరు ఏ పార్లమెంట్ నియోజకవర్గం (లోక్‌సభ స్థానం) పరిధిలో నివసిస్తున్నారు?",
    required="yes")

row("select_one ac", "ac_constituency",
    "Which Assembly Constituency do you live in?",
    "మీరు ఏ శాసనసభ నియోజకవర్గం పరిధిలో నివసిస్తున్నారు?",
    required="yes", choice_filter="pc_filter=${pc_constituency}")

row("select_one age_group", "age_group",
    "What is your age group?", "మీ వయస్సు ఏ వర్గంలోకి వస్తుంది?", required="yes")

row("select_one gender", "gender",
    "What is your gender?", "మీ లింగం ఏమిటి?", required="yes")

row("select_one education", "education",
    "What is the highest level of education you have completed?",
    "మీరు పూర్తి చేసిన అత్యున్నత విద్యార్హత ఏమిటి?", required="yes")

row("select_one last12_activity", "last12_activity",
    "What did you mostly do in the last 12 months?",
    "గత 12 నెలల్లో మీరు ఎక్కువగా ఏం చేస్తూ గడిపారు?", required="yes")

row("text", "last12_activity_other",
    "Please specify", "దయచేసి తెలపండి", relevant="${last12_activity}='other'")

row("select_one occupation", "main_occupation",
    "What is your main occupation (or, if retired, your former occupation)? What work do/did you do?",
    "మీ ముఖ్య వృత్తి ఏమిటి (పదవీ విరమణ పొందినవారైతే, మీ పూర్వ వృత్తి)? మీరు ఏ పని చేస్తారు / చేసేవారు?",
    required="yes",
    hen="Routes the respondent to the matching profession-specific section.",
    hte="ఈ సమాధానం ఆధారంగా సంబంధిత వృత్తి-నిర్దిష్ట విభాగం చూపించబడుతుంది.")

row("select_one work_type", "work_type",
    "What is your employment arrangement?",
    "మీ ఉపాధి స్వభావం ఏమిటి?", required="yes",
    relevant="${last12_activity}='worked'")

row("text", "work_type_other",
    "Please specify", "దయచేసి తెలపండి", relevant="${work_type}='other'")

row("integer", "b03_days_worked_30d",
    "How many days did you work in the last 30 days? (Write 0 if you did not work at all.)",
    "గత 30 రోజుల్లో మీరు ఎన్ని రోజులు పనిచేశారు? పనిచేయకపోతే 0 అని రాయండి.",
    relevant="${last12_activity}='worked'",
    constraint=". >= 0 and . <= 30", cmsg="Enter a number of days between 0 and 30.")

end_group()

# =====================================================================
# SECTION 2: PROFESSION-SPECIFIC MODULE (SAMPLE: WEAVERS)
# Routed by ${main_occupation}. The other 41 profession groups follow the
# exact same pattern and will be added the same way after this sample is approved.
# =====================================================================
row("note", "sec2_title", "SECTION 2: Profession-Specific Questions",
    "విభాగం 2: వృత్తి-ఆధారిత ప్రశ్నలు")

group("grp_prof_weavers", "Weavers", "చేనేత కార్మికులు", relevant="${main_occupation}='weavers'")

row("select_one wv_work_pay_arrangement", "wv_work_pay_arrangement",
    "How do you do your weaving work, and how are you paid?",
    "మీరు మీ నేత పనిని ఎలా చేస్తారు, మరియు మీకు వేతనం ఎలా చెల్లిస్తారు?", required="yes")
row("text", "wv_work_pay_arrangement_other", "Please specify", "దయచేసి తెలపండి", relevant="${wv_work_pay_arrangement}='other'")

row("select_one wv_loom_type_owner", "wv_loom_type_owner",
    "Which loom do you mainly use, and who owns it?",
    "మీరు ప్రధానంగా ఏ మగ్గం ఉపయోగిస్తారు, మరియు అది ఎవరిది?", required="yes")
row("text", "wv_loom_type_owner_other", "Please specify", "దయచేసి తెలపండి", relevant="${wv_loom_type_owner}='other'")

row("integer", "wv_qty_woven",
    "In the last cycle, how many pieces or metres of cloth did you weave?",
    "చివరి ఉత్పత్తి చక్రంలో, మీరు ఎన్ని ముక్కలు లేదా మీటర్ల వస్త్రాన్ని నేశారు?",
    required="yes", constraint=". >= 0",
    hen="\"Last cycle\" means the most recent finished order or production cycle. Write the unit with the number.",
    hte="\"చివరి చక్రం\" అంటే ఇటీవల పూర్తయిన ఆర్డర్ లేదా ఉత్పత్తి చక్రం. యూనిట్‌ను సంఖ్యతో పాటు రాయండి.")
row("select_one wv_unit", "wv_qty_woven_unit",
    "Unit", "యూనిట్", relevant="${wv_qty_woven} != ''")

row("integer", "wv_income_30d",
    "In the last 30 days, how much money did you get from weaving?",
    "గత 30 రోజుల్లో, నేత పని నుండి మీకు ఎంత డబ్బు వచ్చింది?",
    required="yes", constraint=". >= 0",
    hen="Include wages, piece-rate payments and cloth sales.",
    hte="వేతనాలు, ముక్క-రేటు చెల్లింపులు మరియు వస్త్ర అమ్మకాలు కలిపి లెక్కించండి.")

row("text", "wv_last_sale_detail",
    "In the last cycle, what cloth did you weave, how much did you get per piece or metre, and in which month?",
    "చివరి చక్రంలో, మీరు ఏ వస్త్రాన్ని నేశారు, ముక్క లేదా మీటరుకు ఎంత వచ్చింది, మరియు ఏ నెలలో?",
    hen="Example: \"Ponduru khadi, Rs.180 per metre, August\" or \"Cotton saree, Rs.900 per piece, September\".",
    hte="ఉదాహరణ: \"పొందూరు ఖాదీ, మీటరుకు రూ.180, ఆగస్టు\" లేదా \"కాటన్ చీర, ముక్కకు రూ.900, సెప్టెంబర్\".")

row("integer", "wv_out_of_pocket_cost",
    "In the last cycle, how much did you spend from your own pocket on weaving?",
    "చివరి చక్రంలో, నేత పని కోసం మీరు మీ సొంత డబ్బు నుండి ఎంత ఖర్చు చేశారు?",
    required="yes", constraint=". >= 0",
    hen="Include yarn or silk, zari and dyes, warping or sizing, hired helpers, electricity and transport. Enter 0 if the master weaver or cooperative paid everything.",
    hte="దారం/పట్టు, జరీ మరియు రంగులు, వార్పింగ్/సైజింగ్, కూలీలు, విద్యుత్, రవాణా కలిపి లెక్కించండి. మేస్త్రి నేతకారుడు లేదా సహకార సంఘం అంతా చెల్లిస్తే 0 రాయండి.")

row("select_one wv_cloth_buyer", "wv_cloth_buyer",
    "Who took or bought most of your cloth in the last cycle?",
    "చివరి చక్రంలో మీ వస్త్రంలో ఎక్కువ భాగాన్ని ఎవరు తీసుకున్నారు లేదా కొన్నారు?", required="yes")
row("text", "wv_cloth_buyer_other", "Please specify", "దయచేసి తెలపండి", relevant="${wv_cloth_buyer}='other'")

row("select_multiple wv_extra_work", "wv_extra_work",
    "What extra work was done on your cloth before it was sold?",
    "అమ్మకానికి ముందు మీ వస్త్రంపై ఏ అదనపు పని చేయబడింది?", required="yes")
row("text", "wv_extra_work_other", "Please specify", "దయచేసి తెలపండి", relevant="selected(${wv_extra_work},'other')")

row("integer", "wv_loom_idle_days_12m",
    "In the last 12 months, on how many days could your loom not run when you wanted to weave?",
    "గత 12 నెలల్లో, మీరు నేయాలనుకున్నప్పుడు మీ మగ్గం పనిచేయని రోజులు ఎన్ని?",
    required="yes", constraint=". >= 0 and . <= 365",
    hen="Enter 0 if none.", hte="లేకపోతే 0 రాయండి.")

row("integer", "wv_unpaid_family_hours",
    "In the last cycle, how many hours in total did family members help with weaving work without being paid?",
    "చివరి చక్రంలో, కుటుంబ సభ్యులు వేతనం లేకుండా నేత పనిలో సహాయం చేసిన మొత్తం గంటలు ఎన్ని?",
    constraint=". >= 0",
    hen="Include warping, winding, sizing, dyeing and hand spinning. Enter 0 if none.",
    hte="వార్పింగ్, వైండింగ్, సైజింగ్, రంగులు వేయడం, చేతి వడకడం కలిపి లెక్కించండి. లేకపోతే 0 రాయండి.")

row("select_multiple wv_documents_held", "wv_documents_held",
    "Which of these documents do you have now?",
    "మీ వద్ద ప్రస్తుతం ఈ పత్రాలలో ఏవి ఉన్నాయి?", required="yes")
row("text", "wv_documents_held_other", "Please specify", "దయచేసి తెలపండి", relevant="selected(${wv_documents_held},'other')")

row("select_multiple wv_infra_usable", "wv_infra_usable",
    "Which of these can you actually use for weaving?",
    "నేత పని కోసం వీటిలో వేటిని మీరు నిజంగా ఉపయోగించగలరు?", required="yes")
row("text", "wv_infra_usable_other", "Please specify", "దయచేసి తెలపండి", relevant="selected(${wv_infra_usable},'other')")

row("select_multiple wv_skills_self", "wv_skills_self",
    "Which of these can you do well yourself?",
    "వీటిలో వేటిని మీరు స్వయంగా బాగా చేయగలరు?", required="yes")
row("text", "wv_skills_self_other", "Please specify", "దయచేసి తెలపండి", relevant="selected(${wv_skills_self},'other')")

row("select_multiple wv_govt_support_12m", "wv_govt_support_12m",
    "In the last 12 months, which government weaver support did you get?",
    "గత 12 నెలల్లో, మీకు ఏ ప్రభుత్వ చేనేత మద్దతు అందింది?", required="yes")
row("text", "wv_govt_support_12m_other", "Please specify", "దయచేసి తెలపండి", relevant="selected(${wv_govt_support_12m},'other')")

row("select_multiple wv_work_incidents_12m", "wv_work_incidents_12m",
    "In the last 12 months, which of these happened in your work, and did you get any compensation?",
    "గత 12 నెలల్లో, మీ పనిలో వీటిలో ఏవి జరిగాయి, మరియు మీకు ఏదైనా పరిహారం అందిందా?", required="yes")
row("text", "wv_work_incidents_12m_other", "Please specify", "దయచేసి తెలపండి", relevant="selected(${wv_work_incidents_12m},'other')")

end_group()

# ---------------------------------------------------------------------
# Remaining 41 profession modules, built by parallel batch agents from
# the 42 source questionnaires. Each module is a standalone file with
# add_questions(row, group, end_group, note) / add_choices(choice).
# Inserted in the same order as the occupation choice list below.
# ---------------------------------------------------------------------
import importlib.util
import os

_PROF_MODULE_ORDER = [
    "agriculture", "asha_anganwadi", "auto_cab_drivers", "banking_finance", "bureaucrats",
    "cashew", "chartered_accountants", "coffee_plantations", "daily_wage_mgnrega_jaljeevan",
    "ex_defence_staff", "govt_employees_contract", "homemakers", "hospitality_tourism",
    "it_corporate_management", "jaggery", "lawyers_advocates", "manufacturing_msme",
    "marine_fisheries", "mechanics", "medical_personnel", "mining", "ngo_shg",
    "other_unlisted", "police", "political_workers", "quick_commerce", "rtc_workers",
    "ration_dealers", "real_estate", "religious_leaders", "restaurant_workers",
    "retired_persons", "self_employed_entrepreneurs", "social_media_marketing", "students",
    "tailors_garment", "teachers", "toddy_plantation", "transgender", "transport_business",
    "unemployed_jobseekers",
]

_PROF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profession_modules")
_loaded_prof_modules = []
for _occ in _PROF_MODULE_ORDER:
    _path = os.path.join(_PROF_DIR, f"prof_{_occ}.py")
    _spec = importlib.util.spec_from_file_location(f"prof_{_occ}", _path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    assert _mod.OCC_CODE == _occ, f"OCC_CODE mismatch in {_path}: {_mod.OCC_CODE!r} != {_occ!r}"
    _loaded_prof_modules.append(_mod)

for _mod in _loaded_prof_modules:
    _mod.add_questions(row, group, end_group, note)

# =====================================================================
# SECTION 3: POLITICAL INCLINATION & EXPECTATIONS (common to all)
# Hard cap: 5-10 questions per the client's total-interview-length
# directive. Every theme from the client's explicit keep-list is
# preserved, each compressed to its single most essential question:
# priority problem, responsibility, trust+satisfaction (merged),
# scheme awareness funnel, welfare prev-vs-current comparison,
# complaint-channel awareness, facility access, leader quality,
# reservation opinion, and main information source (media + social
# media merged into one).
# =====================================================================
row("note", "sec3_title", "SECTION 3: Political Inclination & Expectations",
    "విభాగం 3: రాజకీయ అభిప్రాయాలు మరియు అంచనాలు")

group("grp_political", "Political Inclination & Expectations", "రాజకీయ అభిప్రాయాలు మరియు అంచనాలు")

row("select_one priority_problem", "pol_priority_problem",
    "What is the single biggest problem in your area that needs government attention?",
    "ప్రభుత్వం దృష్టి పెట్టాల్సిన మీ ప్రాంతంలో అతిపెద్ద సమస్య ఏమిటి?", required="yes")
row("text", "pol_priority_problem_other", "Please specify", "దయచేసి తెలపండి", relevant="${pol_priority_problem}='other'")

row("select_one responsible_party", "pol_responsible_party",
    "Who do you think is mainly responsible for fixing it?",
    "దీన్ని పరిష్కరించాల్సిన బాధ్యత ప్రధానంగా ఎవరిదని మీరు భావిస్తున్నారు?", required="yes")

row("select_one trust_satisfaction", "pol_trust_satisfaction",
    "Overall, how much do you trust the government (local, state and central together) to solve problems like yours?",
    "మొత్తంగా, మీలాంటి వారి సమస్యలను పరిష్కరించడంలో ప్రభుత్వంపై (స్థానిక, రాష్ట్ర, కేంద్రం కలిపి) మీకు ఎంత నమ్మకం ఉంది?",
    required="yes")

row("select_one scheme_awareness_funnel", "pol_scheme_awareness",
    "Thinking of government welfare schemes you may be eligible for, which best describes you?",
    "మీరు అర్హులైన ప్రభుత్వ సంక్షేమ పథకాల గురించి ఆలోచిస్తే, మీకు ఏది సరిపోతుంది?", required="yes")

row("select_one welfare_compare_govts", "pol_welfare_govt_compare",
    "Compared to the previous government, how do you rate the current government on welfare benefits reaching people?",
    "మునుపటి ప్రభుత్వంతో పోలిస్తే, సంక్షేమ ప్రయోజనాలు ప్రజలకు చేరడంలో ప్రస్తుత ప్రభుత్వాన్ని మీరు ఎలా రేట్ చేస్తారు?", required="yes")

row("select_one welfare_availed", "pol_welfare_received",
    "In the last 12 months, did you or your family receive any welfare scheme benefit?",
    "గత 12 నెలల్లో, మీరు లేదా మీ కుటుంబం ఏదైనా సంక్షేమ పథక ప్రయోజనం పొందారా?", required="yes")
row("text", "pol_welfare_received_name", "If yes, please name the scheme", "అవును అయితే, ఆ పథకం పేరు తెలపండి", relevant="${pol_welfare_received}='yes'")

row("select_one health_104_108", "pol_104_108_awareness",
    "Do you know about the 104/108 mobile health and emergency services, and have you used them?",
    "104/108 మొబైల్ ఆరోగ్య మరియు అత్యవసర సేవల గురించి మీకు తెలుసా? వాటిని ఉపయోగించారా?", required="yes")

row("select_one complaint_channel", "pol_complaint_channel",
    "If you had a problem, how would you submit a complaint to the government?",
    "మీకు ఏదైనా సమస్య వస్తే, ప్రభుత్వానికి ఫిర్యాదును మీరు ఎలా సమర్పిస్తారు?", required="yes")
row("text", "pol_complaint_channel_other", "Please specify", "దయచేసి తెలపండి", relevant="${pol_complaint_channel}='other'")

row("select_one complaint_satisfaction", "pol_complaint_satisfaction",
    "How satisfied are you with the way government complaints are handled in your area?",
    "మీ ప్రాంతంలో ప్రభుత్వ ఫిర్యాదులు పరిష్కరించే విధానంతో మీరు ఎంత సంతృప్తిగా ఉన్నారు?", required="yes")

row("select_multiple facilities_unused", "pol_facilities_unused",
    "Which of these facilities are in your area, but you could not fully use for your work in the last 12 months?",
    "గత 12 నెలల్లో మీ ప్రాంతంలో ఉన్నా మీరు మీ పని కోసం పూర్తిగా వాడుకోలేకపోయిన సౌకర్యాలు ఏవి?", required="yes")
row("text", "pol_facilities_unused_other", "Please specify", "దయచేసి తెలపండి", relevant="selected(${pol_facilities_unused},'other')")

row("select_one leader_quality", "pol_leader_quality",
    "Which quality matters the most to you when choosing your local leader?",
    "మీ స్థానిక నాయకుడిని ఎంచుకునేటప్పుడు మీకు ఏ లక్షణం అత్యంత ముఖ్యమైనది?", required="yes")

row("select_one reservation_opinion", "pol_reservation_opinion",
    "In your opinion, should the reservation quota for SC, ST and BC be altered?",
    "మీ అభిప్రాయం ప్రకారం, SC, ST, BC రిజర్వేషన్ కోటాను మార్చాలా?", required="yes")

row("select_one dev_env_priority", "pol_dev_env_priority",
    "When tension arises between industrial development and environmental protection, which should take priority?",
    "పారిశ్రామిక అభివృద్ధికి, పర్యావరణ పరిరక్షణకు మధ్య వైరుధ్యం తలెత్తినప్పుడు, దేనికి ప్రాధాన్యత ఇవ్వాలి?", required="yes")

row("select_one info_source", "pol_main_info_source",
    "What is your main source of news and information? (TV, newspaper, radio, social media, word of mouth)",
    "వార్తలు మరియు సమాచారం కోసం మీ ప్రధాన మూలం ఏమిటి? (టీవీ, వార్తాపత్రిక, రేడియో, సోషల్ మీడియా, నోటిమాటగా)", required="yes")

row("select_one social_platform", "pol_main_social_platform",
    "If social media, which platform do you use most?",
    "సోషల్ మీడియా అయితే, మీరు ఎక్కువగా ఏ ప్లాట్‌ఫామ్ వాడతారు?",
    relevant="${pol_main_info_source}='social_media'")

end_group()


# =====================================================================
# CHOICES
# =====================================================================
ws2 = wb.create_sheet("choices")
ws2.append(CHOICE_COLS)
def choice(list_name, name, en, te, pc_filter="", occ_filter=""):
    ws2.append([list_name, name, en, te, pc_filter, occ_filter])

choice("pc", "visakhapatnam", "Visakhapatnam", "విశాఖపట్నం")
choice("pc", "anakapalli", "Anakapalli", "అనకాపల్లి")
choice("pc", "srikakulam", "Srikakulam", "శ్రీకాకుళం")
choice("pc", "vizianagaram", "Vizianagaram", "విజయనగరం")
choice("pc", "araku", "Araku (ST) - Covers Parvathipuram Manyam", "అరకు (ఎస్టీ) - పార్వతీపురం మాన్యం కలిపి")

ac_list = [
    ("gajuwaka", "Gajuwaka", "గాజువాక", "visakhapatnam"),
    ("bhimli", "Bhimli", "భీమిలి", "visakhapatnam"),
    ("srungavarapukota", "Srungavarapukota", "శృంగవరపుకోట", "visakhapatnam"),
    ("visakhapatnam_south", "Visakhapatnam South", "విశాఖపట్నం దక్షిణ", "visakhapatnam"),
    ("visakhapatnam_north", "Visakhapatnam North", "విశాఖపట్నం ఉత్తర", "visakhapatnam"),
    ("visakhapatnam_east", "Visakhapatnam East", "విశాఖపట్నం తూర్పు", "visakhapatnam"),
    ("visakhapatnam_west", "Visakhapatnam West", "విశాఖపట్నం పశ్చిమ", "visakhapatnam"),
    ("anakapalle", "Anakapalle", "అనకాపల్లె", "anakapalli"),
    ("madugula", "Madugula", "మాడుగుల", "anakapalli"),
    ("narsipatnam", "Narsipatnam", "నర్సీపట్నం", "anakapalli"),
    ("chodavaram", "Chodavaram", "చోడవరం", "anakapalli"),
    ("payakaraopet", "Payakaraopet", "పాయకరావుపేట", "anakapalli"),
    ("pendurthi", "Pendurthi", "పెందుర్తి", "anakapalli"),
    ("elamanchili", "Elamanchili", "ఎలమంచిలి", "anakapalli"),
    ("narasannapeta", "Narasannapeta", "నరసన్నపేట", "srikakulam"),
    ("srikakulam_ac", "Srikakulam", "శ్రీకాకుళం", "srikakulam"),
    ("tekkali", "Tekkali", "తెక్కలి", "srikakulam"),
    ("pathapatnam", "Pathapatnam", "పాతపట్నం", "srikakulam"),
    ("ichchapuram", "Ichchapuram", "ఇచ్చాపురం", "srikakulam"),
    ("palasa", "Palasa", "పలాస", "srikakulam"),
    ("amadalavalasa", "Amadalavalasa", "ఆమదాలవలస", "srikakulam"),
    ("cheepurupalle", "Cheepurupalle", "చీపురుపల్లి", "vizianagaram"),
    ("bobbili", "Bobbili", "బొబ్బిలి", "vizianagaram"),
    ("gajapathinagaram", "Gajapathinagaram", "గజపతినగరం", "vizianagaram"),
    ("etcherla", "Etcherla", "ఎచ్చెర్ల", "vizianagaram"),
    ("nellimarla", "Nellimarla", "నెల్లిమర్ల", "vizianagaram"),
    ("rajam", "Rajam", "రాజాం", "vizianagaram"),
    ("vizianagaram_ac", "Vizianagaram", "విజయనగరం", "vizianagaram"),
    ("rampachodavaram", "Rampachodavaram", "రంపచోడవరం", "araku"),
    ("paderu", "Paderu", "పాడేరు", "araku"),
    ("kurupam", "Kurupam", "కురుపాం", "araku"),
    ("araku_valley", "Araku valley", "అరకు లోయ", "araku"),
    ("palakonda", "Palakonda", "పాలకొండ", "araku"),
    ("salur", "Salur", "సాలూరు", "araku"),
    ("parvathipuram", "Parvathipuram", "పార్వతీపురం", "araku"),
]
for name, en, te, pc in ac_list:
    choice("ac", name, en, te, pc)

choice("yesno_dk", "yes", "Yes", "అవును")
choice("yesno_dk", "no", "No", "కాదు")
choice("yesno_dk", "dont_know", "Don't know", "తెలియదు")

choice("yesno", "yes", "Yes", "అవును")
choice("yesno", "no", "No", "కాదు")

choice("yesno_notsure", "yes", "Yes", "అవును")
choice("yesno_notsure", "no", "No", "కాదు")
choice("yesno_notsure", "not_sure", "Not sure about eligibility", "అర్హత గురించి ఖచ్చితంగా తెలియదు")

for name, en, te in [
    ("16_18", "16-18", "16-18"), ("19_25", "19-25", "19-25"), ("26_35", "26-35", "26-35"),
    ("36_50", "36-50", "36-50"), ("51_60", "51-60", "51-60"),
    ("61_plus", "61 and above", "61 మరియు అంతకంటే ఎక్కువ"),
]:
    choice("age_group", name, en, te)

choice("gender", "male", "Male", "పురుషుడు")
choice("gender", "female", "Female", "స్త్రీ")
choice("gender", "other", "Others", "ఇతరులు")
choice("gender", "pns", "Prefer not to say", "చెప్పదలచుకోలేదు")

choice("education", "no_formal_schooling", "No formal schooling", "అధికారిక విద్య లేదు")
choice("education", "primary", "Primary (1-5)", "ప్రాథమిక (1-5)")
choice("education", "middle", "Middle (6-8)", "మధ్యస్థాయి (6-8)")
choice("education", "secondary", "Secondary (9-10)", "సెకండరీ (9-10)")
choice("education", "intermediate_diploma", "Intermediate / Diploma", "ఇంటర్మీడియట్ / డిప్లొమా")
choice("education", "graduate", "Graduate", "గ్రాడ్యుయేట్")
choice("education", "postgraduate", "Postgraduate and above", "పోస్ట్ గ్రాడ్యుయేట్ మరియు ఆ పై")

choice("govt_private", "government", "Government institution", "ప్రభుత్వ సంస్థ")
choice("govt_private", "private", "Private institution", "ప్రైవేటు సంస్థ")

choice("community", "general", "General", "జనరల్")
choice("community", "obc", "Other Backward Classes (OBC)", "ఇతర వెనుకబడిన తరగతులు (OBC)")
choice("community", "sc", "Scheduled Caste (SC)", "షెడ్యూల్డ్ కులం (SC)")
choice("community", "st", "Scheduled Tribes (ST)", "షెడ్యూల్డ్ తరగతి (ST)")
choice("community", "ews", "Economic Weaker Section", "ఆర్థికంగా వెనుకబడిన వర్గం (EWS)")
choice("community", "pns", "Don't want to say", "చెప్పదలచుకోలేదు")

# ---- New shared-layer choice lists (Section 1 rebuild) ----
months = [
    ("jan", "January", "జనవరి"), ("feb", "February", "ఫిబ్రవరి"), ("mar", "March", "మార్చి"),
    ("apr", "April", "ఏప్రిల్"), ("may", "May", "మే"), ("jun", "June", "జూన్"),
    ("jul", "July", "జూలై"), ("aug", "August", "ఆగస్టు"), ("sep", "September", "సెప్టెంబర్"),
    ("oct", "October", "అక్టోబర్"), ("nov", "November", "నవంబర్"), ("dec", "December", "డిసెంబర్"),
]
for name, en, te in months:
    choice("months_list", name, en, te)

choice("social_protection", "pf", "Provident Fund (PF)", "భవిష్య నిధి (PF)")
choice("social_protection", "esi", "ESI (health insurance from employer)", "ESI (యజమాని ఇచ్చే ఆరోగ్య బీమా)")
choice("social_protection", "accident_health_insurance", "Accident or health insurance", "ప్రమాద లేదా ఆరోగ్య బీమా")
choice("social_protection", "pension", "Pension", "పింఛను")
choice("social_protection", "paid_leave", "Paid leave", "జీతంతో కూడిన సెలవు")
choice("social_protection", "eshram_welfare_card", "e-Shram or welfare board card", "ఈ-శ్రమ్ లేదా సంక్షేమ బోర్డు కార్డు")
choice("social_protection", "none", "None of these", "వీటిలో ఏదీ లేదు")

choice("income_trend", "higher", "Higher", "ఎక్కువగా ఉంది")
choice("income_trend", "same", "Same", "యథాతథంగా ఉంది")
choice("income_trend", "lower", "Lower", "తక్కువగా ఉంది")

choice("certificate_issuer", "government", "Government department or board", "ప్రభుత్వ శాఖ లేదా బోర్డు")
choice("certificate_issuer", "private_institute", "Private training institute or company", "ప్రైవేటు శిక్షణ సంస్థ లేదా కంపెనీ")
choice("certificate_issuer", "cooperative_society", "Cooperative or producer society", "సహకార సంఘం లేదా ఉత్పత్తిదారుల సంఘం")
choice("certificate_issuer", "ngo", "NGO", "స్వచ్ఛంద సంస్థ (NGO)")
choice("certificate_issuer", "other", "Other", "ఇతర")

choice("training_provider", "government", "Government department", "ప్రభుత్వ శాఖ")
choice("training_provider", "ngo", "NGO", "స్వచ్ఛంద సంస్థ (NGO)")
choice("training_provider", "private_institute", "Private company or institute", "ప్రైవేటు కంపెనీ లేదా సంస్థ")
choice("training_provider", "cooperative_society", "Cooperative or society", "సహకార సంఘం")
choice("training_provider", "employer", "Employer", "యజమాని")
choice("training_provider", "other", "Other", "ఇతర")

barriers_list = [
    ("skills", "Skills", "నైపుణ్యాలు"),
    ("certification", "Certification", "సర్టిఫికేషన్"),
    ("awareness_of_schemes", "Awareness of government schemes", "ప్రభుత్వ పథకాల గురించి అవగాహన"),
    ("finance", "Finance", "ఆర్థిక సహాయం"),
    ("market_or_price", "Market or price", "మార్కెట్ లేదా ధర"),
    ("transport_or_infrastructure", "Transport or infrastructure", "రవాణా లేదా మౌలిక సదుపాయాలు"),
    ("land_or_licence_rights", "Land or licence rights", "భూమి లేదా లైసెన్స్ హక్కులు"),
    ("family_or_social_limits", "Family or social limits", "కుటుంబ లేదా సామాజిక పరిమితులు"),
    ("health", "Health", "ఆరోగ్యం"),
    ("none", "None", "ఏదీ లేదు"),
]
for name, en, te in barriers_list:
    choice("barriers", name, en, te)

choice("borrow_source", "bank", "Bank", "బ్యాంకు")
choice("borrow_source", "shg_cooperative", "Self-help group or cooperative", "స్వయం సహాయక సంఘం లేదా సహకార సంఘం")
choice("borrow_source", "moneylender", "Moneylender", "వడ్డీ వ్యాపారి")
choice("borrow_source", "relatives_friends", "Relatives or friends", "బంధువులు లేదా స్నేహితులు")
choice("borrow_source", "employer_trader_advance", "Employer or trader advance", "యజమాని లేదా వ్యాపారి అడ్వాన్సు")
choice("borrow_source", "do_not_borrow", "Do not borrow", "అప్పు తీసుకోరు")
choice("borrow_source", "other", "Other", "ఇతర")

choice("borrow_outcome", "full_amount", "Got the full amount", "పూర్తి మొత్తం వచ్చింది")
choice("borrow_outcome", "part_amount", "Got part of the amount", "కొంత మొత్తం వచ్చింది")
choice("borrow_outcome", "refused", "Refused", "తిరస్కరించారు")

choice("travel_mode", "walk", "Walk", "నడక")
choice("travel_mode", "bicycle", "Bicycle", "సైకిల్")
choice("travel_mode", "bus", "Bus", "బస్సు")
choice("travel_mode", "auto_shared", "Auto or shared auto", "ఆటో లేదా షేర్డ్ ఆటో")
choice("travel_mode", "own_vehicle", "Own two/four-wheeler", "సొంత వాహనం")
choice("travel_mode", "other", "Other", "ఇతర")

choice("rights_document", "land_title_pattadar", "Land title / Pattadar passbook", "భూమి హక్కు పత్రం / పట్టాదారు పాస్ బుక్")
choice("rights_document", "tenancy_card_ccrc", "Tenancy card (CCRC)", "కౌలు కార్డు (CCRC)")
choice("rights_document", "trade_vendor_licence", "Trade or vendor licence", "వ్యాపార లేదా వెండర్ లైసెన్స్")
choice("rights_document", "profession_specific_card", "Profession-specific card (weaver, fisher, artisan, etc.)", "వృత్తి-నిర్దిష్ట కార్డు (చేనేత, మత్స్యకార, హస్తకళాకారుల కార్డు వంటివి)")
choice("rights_document", "business_registration", "Business registration", "వ్యాపార నమోదు")
choice("rights_document", "other", "Other", "ఇతర")

choice("application_status", "pending", "Pending", "పెండింగ్‌లో ఉంది")
choice("application_status", "approved", "Approved", "ఆమోదించబడింది")
choice("application_status", "rejected", "Rejected", "తిరస్కరించబడింది")
choice("application_status", "not_sure", "Not sure", "ఖచ్చితంగా తెలియదు")

choice("future_plan", "same_work_here", "Same work here", "ఇక్కడే ఇదే పనిలో కొనసాగడం")
choice("future_plan", "other_work_here", "Other work here", "ఇక్కడే వేరే పని")
choice("future_plan", "other_city", "Another city", "మరో నగరం")
choice("future_plan", "abroad", "Abroad", "విదేశం")
choice("future_plan", "not_sure", "Not sure", "ఖచ్చితంగా తెలియదు")

choice("conditions_to_stay", "better_pay", "Better pay here", "ఇక్కడ మెరుగైన వేతనం")
choice("conditions_to_stay", "steady_work", "Steadier work here", "ఇక్కడ స్థిరమైన పని")
choice("conditions_to_stay", "training_opportunity", "A training opportunity here", "ఇక్కడ శిక్షణ అవకాశం")
choice("conditions_to_stay", "local_employer", "A good local employer", "మంచి స్థానిక యజమాని")
choice("conditions_to_stay", "family_reasons", "Family or social reasons to stay", "కుటుంబ లేదా సామాజిక కారణాలు")
choice("conditions_to_stay", "other", "Other", "ఇతర")

choice("migration_destination", "within_district", "Within the district", "జిల్లాలోనే")
choice("migration_destination", "another_district_ap", "Another district in AP", "ఆంధ్రప్రదేశ్‌లోని మరో జిల్లా")
choice("migration_destination", "another_state", "Another state", "మరో రాష్ట్రం")
choice("migration_destination", "abroad", "Abroad", "విదేశం")
choice("migration_destination", "other", "Other", "ఇతర")

choice("migration_reason", "no_local_work", "No local work", "స్థానికంగా పని లేదు")
choice("migration_reason", "low_local_pay", "Local pay too low", "స్థానిక వేతనం తక్కువ")
choice("migration_reason", "better_fixed_wage", "Better or fixed wage elsewhere", "వేరే చోట మెరుగైన లేదా స్థిరమైన వేతనం")
choice("migration_reason", "education", "Education", "విద్య")
choice("migration_reason", "family_reasons", "Family reasons", "కుటుంబ కారణాలు")
choice("migration_reason", "other", "Other", "ఇతర")

choice("rejection_reason", "lacked_required_skill", "Lacked the required skill", "అవసరమైన నైపుణ్యం లేదు")
choice("rejection_reason", "no_local_vacancies", "No local vacancies", "స్థానికంగా ఖాళీలు లేవు")
choice("rejection_reason", "preferred_local_candidate", "Employer preferred another candidate", "యజమాని వేరే అభ్యర్థిని ఎంచుకున్నారు")
choice("rejection_reason", "asked_for_bribe_connections", "Asked for a bribe or connections", "లంచం లేదా పరిచయాలు అడిగారు")
choice("rejection_reason", "overqualified", "Considered overqualified", "అధిక అర్హత ఉన్నట్లు భావించారు")
choice("rejection_reason", "age", "Age", "వయస్సు")
choice("rejection_reason", "other", "Other", "ఇతర")

choice("business_constraint", "lack_of_finance", "Lack of finance or capital", "ఆర్థిక సహాయం లేదా మూలధనం లేమి")
choice("business_constraint", "skilled_worker_shortage", "Difficulty finding skilled workers", "నైపుణ్యం గల కార్మికులను కనుగొనడంలో కష్టం")
choice("business_constraint", "market_demand_competition", "Market demand or competition", "మార్కెట్ డిమాండ్ లేదా పోటీ")
choice("business_constraint", "infrastructure", "Infrastructure", "మౌలిక సదుపాయాలు")
choice("business_constraint", "govt_rules_compliance", "Government rules or compliance", "ప్రభుత్వ నిబంధనలు లేదా వర్తింపు")
choice("business_constraint", "other", "Other", "ఇతర")

choice("resource_readiness", "training", "Training", "శిక్షణ")
choice("resource_readiness", "equipment", "Equipment", "పరికరాలు")
choice("resource_readiness", "loan", "A loan", "రుణం")
choice("resource_readiness", "guaranteed_buyer", "A guaranteed buyer", "హామీతో కూడిన కొనుగోలుదారు")
choice("resource_readiness", "not_interested", "Not interested", "ఆసక్తి లేదు")

# Resource-linked skills per constituency (simplified placeholder -- see note in survey sheet)
choice("resource_skill", "araku_coffee_pruning", "Coffee: pruning and shade management", "కాఫీ: కత్తిరింపు మరియు నీడ నిర్వహణ", pc_filter="araku")
choice("resource_skill", "araku_coffee_processing", "Coffee: pulping, drying and grading", "కాఫీ: పల్పింగ్, ఎండబెట్టడం, గ్రేడింగ్", pc_filter="araku")
choice("resource_skill", "araku_forest_produce", "Forest produce collection and processing", "అటవీ ఉత్పత్తుల సేకరణ మరియు ప్రాసెసింగ్", pc_filter="araku")
choice("resource_skill", "none", "None of these", "వీటిలో ఏదీ లేదు", pc_filter="araku")
choice("resource_skill", "srikakulam_cashew_grading", "Cashew: sorting and grading", "జీడిమామిడి: సార్టింగ్ మరియు గ్రేడింగ్", pc_filter="srikakulam")
choice("resource_skill", "srikakulam_cashew_processing", "Cashew: roasting and kernel extraction", "జీడిమామిడి: వేయించడం మరియు గింజ తీయడం", pc_filter="srikakulam")
choice("resource_skill", "srikakulam_handloom", "Handloom weaving or finishing", "చేనేత లేదా ఫినిషింగ్ పని", pc_filter="srikakulam")
choice("resource_skill", "none", "None of these", "వీటిలో ఏదీ లేదు", pc_filter="srikakulam")
choice("resource_skill", "vizianagaram_cashew_grading", "Cashew: sorting and grading", "జీడిమామిడి: సార్టింగ్ మరియు గ్రేడింగ్", pc_filter="vizianagaram")
choice("resource_skill", "vizianagaram_mango_processing", "Mango: grading and processing", "మామిడి: గ్రేడింగ్ మరియు ప్రాసెసింగ్", pc_filter="vizianagaram")
choice("resource_skill", "vizianagaram_handloom", "Handloom weaving or finishing", "చేనేత లేదా ఫినిషింగ్ పని", pc_filter="vizianagaram")
choice("resource_skill", "none", "None of these", "వీటిలో ఏదీ లేదు", pc_filter="vizianagaram")
choice("resource_skill", "visakhapatnam_fish_processing", "Marine fish: sorting, drying or salting", "సముద్ర చేపలు: సార్టింగ్, ఎండబెట్టడం లేదా ఉప్పు వేయడం", pc_filter="visakhapatnam")
choice("resource_skill", "visakhapatnam_fish_boat", "Boat or net repair", "పడవ లేదా వల మరమ్మతు", pc_filter="visakhapatnam")
choice("resource_skill", "visakhapatnam_engineering", "Machine operation or engineering trade skill", "యంత్ర నిర్వహణ లేదా ఇంజనీరింగ్ నైపుణ్యం", pc_filter="visakhapatnam")
choice("resource_skill", "none", "None of these", "వీటిలో ఏదీ లేదు", pc_filter="visakhapatnam")
choice("resource_skill", "anakapalli_cashew_grading", "Cashew: sorting and grading", "జీడిమామిడి: సార్టింగ్ మరియు గ్రేడింగ్", pc_filter="anakapalli")
choice("resource_skill", "anakapalli_mango_processing", "Mango: grading and processing", "మామిడి: గ్రేడింగ్ మరియు ప్రాసెసింగ్", pc_filter="anakapalli")
choice("resource_skill", "anakapalli_fish_processing", "Marine fish: sorting, drying or salting", "సముద్ర చేపలు: సార్టింగ్, ఎండబెట్టడం లేదా ఉప్పు వేయడం", pc_filter="anakapalli")
choice("resource_skill", "none", "None of these", "వీటిలో ఏదీ లేదు", pc_filter="anakapalli")

choice("last12_activity", "worked", "Worked for pay or profit (job, business, farming, daily wage, own work)", "వేతనం/లాభం కోసం పనిచేశారు (ఉద్యోగం, వ్యాపారం, వ్యవసాయం, దినసరి కూలి, స్వంత పని)")
choice("last12_activity", "looked_for_work", "Looked for work or wanted work", "పని వెతికారు లేదా పని కావాలనుకున్నారు")
choice("last12_activity", "studied", "Studied", "చదువుకున్నారు")
choice("last12_activity", "home_family", "Looked after the home and family", "ఇల్లు, కుటుంబాన్ని చూసుకున్నారు")
choice("last12_activity", "retired", "Retired", "పదవీ విరమణ పొందారు")
choice("last12_activity", "unable_to_work", "Unable to work (illness or disability)", "పనిచేయలేని స్థితి (అనారోగ్యం లేదా వైకల్యం)")
choice("last12_activity", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("work_type", "salaried", "Salaried (regular monthly salary, government or private)", "జీతం ఆధారిత (ప్రభుత్వ లేదా ప్రైవేటు నెలవారీ జీతం)")
choice("work_type", "daily_wage_casual", "Daily wage or casual worker", "దినసరి కూలి లేదా తాత్కాలిక కార్మికుడు")
choice("work_type", "contract_gig", "Contract or gig worker (paid per task, trip or delivery)", "కాంట్రాక్టు లేదా గిగ్ కార్మికుడు (పని, ట్రిప్ లేదా డెలివరీకి చెల్లింపు)")
choice("work_type", "self_employed", "Self-employed, working alone or with family", "స్వయం ఉపాధి, ఒంటరిగా లేదా కుటుంబంతో")
choice("work_type", "employer", "Own business with paid workers (employer)", "జీతం ఇచ్చే కార్మికులతో స్వంత వ్యాపారం (యజమాని)")
choice("work_type", "unpaid_family", "Unpaid family worker (on family farm or business, no pay of your own)", "కుటుంబంలో వేతనం లేని కార్మికుడు (కుటుంబ వ్యవసాయం/వ్యాపారంలో)")
choice("work_type", "other", "Other (specify)", "ఇతర (తెలపండి)")

# Occupation list -- matches the 42 profession questionnaire files exactly.
occ_list = [
    ("agriculture", "Agriculture & Allied Sector", "వ్యవసాయం మరియు అనుబంధ రంగం"),
    ("asha_anganwadi", "ASHA / Anganwadi Workers", "ఆశా / అంగన్‌వాడీ కార్యకర్తలు"),
    ("auto_cab_drivers", "Auto & Cab Drivers", "ఆటో మరియు క్యాబ్ డ్రైవర్లు"),
    ("banking_finance", "Banking & Finance", "బ్యాంకింగ్ మరియు ఆర్థిక రంగం"),
    ("bureaucrats", "Bureaucrats / Government Officers", "ప్రభుత్వ ఉన్నతాధికారులు"),
    ("cashew", "Cashew Cultivation & Processing", "జీడిమామిడి సాగు మరియు ప్రాసెసింగ్"),
    ("chartered_accountants", "Chartered Accountants", "చార్టర్డ్ అకౌంటెంట్లు"),
    ("coffee_plantations", "Coffee Plantations", "కాఫీ తోటలు"),
    ("daily_wage_mgnrega_jaljeevan", "Daily Wage / MGNREGA / Jal Jeevan Workers", "దినసరి కూలీలు / ఉపాధి హామీ (MGNREGA) / జల్ జీవన్ కార్మికులు"),
    ("ex_defence_staff", "Ex-Defence Staff / Veterans", "విశ్రాంత సైనిక సిబ్బంది (మాజీ సైనికులు)"),
    ("govt_employees_contract", "Government Employees / Contract Staff", "ప్రభుత్వ ఉద్యోగులు / కాంట్రాక్టు సిబ్బంది"),
    ("homemakers", "Homemakers", "గృహిణులు"),
    ("hospitality_tourism", "Hospitality & Tourism", "హాస్పిటాలిటీ మరియు పర్యాటక రంగం"),
    ("it_corporate_management", "IT / Corporate / Management Professionals", "ఐటీ / కార్పొరేట్ / యాజమాన్య నిపుణులు"),
    ("jaggery", "Jaggery Production & Trade", "బెల్లం తయారీ మరియు వ్యాపారం"),
    ("lawyers_advocates", "Lawyers / Advocates", "న్యాయవాదులు"),
    ("manufacturing_msme", "Manufacturing / MSMEs", "తయారీ రంగం / సూక్ష్మ-చిన్న-మధ్యతరహా పరిశ్రమలు"),
    ("marine_fisheries", "Marine & Inland Fisheries", "సముద్ర మరియు లోతట్టు మత్స్య సంపద"),
    ("mechanics", "Mechanics", "మెకానిక్‌లు"),
    ("medical_personnel", "Medical Personnel", "వైద్య సిబ్బంది"),
    ("mining", "Mining", "గనుల తవ్వకం (మైనింగ్)"),
    ("ngo_shg", "NGOs / Self-Help Groups", "స్వచ్ఛంద సంస్థలు (NGO) / స్వయం సహాయక సంఘాలు (SHG)"),
    ("other_unlisted", "Other / Unlisted Profession", "ఇతర వృత్తులు (జాబితాలో లేనివి)"),
    ("police", "Police", "పోలీసు"),
    ("political_workers", "Political Workers", "రాజకీయ కార్యకర్తలు"),
    ("quick_commerce", "Quick Commerce Workers", "క్విక్ కామర్స్ కార్మికులు"),
    ("rtc_workers", "RTC Workers (Road Transport Corporation)", "ఆర్టీసీ కార్మికులు"),
    ("ration_dealers", "Ration Dealers", "రేషన్ డీలర్లు"),
    ("real_estate", "Real Estate", "రియల్ ఎస్టేట్"),
    ("religious_leaders", "Religious Leaders", "మతపరమైన నాయకులు"),
    ("restaurant_workers", "Restaurant Workers & Owners", "రెస్టారెంట్ కార్మికులు మరియు యజమానులు"),
    ("retired_persons", "Retired Persons", "పదవీ విరమణ పొందినవారు"),
    ("self_employed_entrepreneurs", "Self-Employed / Entrepreneurs", "స్వయం ఉపాధి మరియు వ్యాపారవేత్తలు"),
    ("social_media_marketing", "Social Media & Marketing", "సోషల్ మీడియా మరియు మార్కెటింగ్"),
    ("students", "Students", "విద్యార్థులు"),
    ("tailors_garment", "Tailors & Garment Merchants", "టైలర్లు మరియు వస్త్ర వ్యాపారులు"),
    ("teachers", "Teachers", "ఉపాధ్యాయులు"),
    ("toddy_plantation", "Toddy Tapping / Plantation", "కల్లు గీత (టాడీ) పరిశ్రమ"),
    ("transgender", "Transgender Persons", "లింగమార్పిడి వ్యక్తులు"),
    ("transport_business", "Transport Business Operators", "రవాణా వ్యాపార నిర్వాహకులు"),
    ("unemployed_jobseekers", "Unemployed / Jobseekers", "నిరుద్యోగులు / ఉద్యోగార్థులు"),
    ("weavers", "Weavers", "చేనేత కార్మికులు"),
]
for name, en, te in occ_list:
    choice("occupation", name, en, te)

# ---- B09 dynamic skills-can-do list: one shared question, filtered per
# occupation by occ_filter. 6-10 observable/demonstrable skills per
# profession, plus "None", per the Drafting Guide's "What your team
# provides for the common questions" rule. ----
B09_SKILLS = {
    "weavers": [
        ("jamdani_buta", "Jamdani or buta work by hand", "చేతితో జామ్‌దానీ లేదా బూటా పని"),
        ("ikat_tiedye", "Ikat tie-and-dye layout", "ఇకత్ టై-అండ్-డై డిజైన్"),
        ("jacquard_weaving", "Jacquard weaving", "జాకార్డ్ నేత"),
        ("warping_sizing", "Warping and sizing", "వార్పింగ్ మరియు సైజింగ్"),
        ("natural_dyeing", "Natural dyeing", "సహజ రంగుల డైయింగ్"),
        ("loom_repair", "Loom repair", "మగ్గం మరమ్మతు"),
        ("design_pattern", "Design and pattern making", "డిజైన్ మరియు నమూనా తయారీ"),
        ("costing_online_selling", "Costing and online selling", "ధర నిర్ణయం మరియు ఆన్‌లైన్ అమ్మకం"),
    ],
    "agriculture": [
        ("seed_selection", "Seed selection and treatment", "విత్తన ఎంపిక మరియు శుద్ధి"),
        ("soil_fertiliser", "Soil testing and fertiliser dosing", "నేల పరీక్ష మరియు ఎరువుల మోతాదు"),
        ("irrigation_scheduling", "Irrigation scheduling", "నీటిపారుదల ప్రణాళిక"),
        ("pest_disease_id", "Pest and disease identification", "చీడపీడలు మరియు వ్యాధుల గుర్తింపు"),
        ("grading_postharvest", "Grading and post-harvest handling", "గ్రేడింగ్ మరియు కోత అనంతర నిర్వహణ"),
        ("machinery_operation", "Farm machinery operation", "వ్యవసాయ యంత్రాల నిర్వహణ"),
        ("organic_methods", "Organic or natural farming methods", "సేంద్రియ లేదా ప్రకృతి వ్యవసాయ పద్ధతులు"),
        ("livestock_care", "Livestock care", "పశువుల సంరక్షణ"),
    ],
    "asha_anganwadi": [
        ("home_visits_counselling", "Home visits and health counselling", "ఇంటింటి సందర్శన మరియు ఆరోగ్య సలహా"),
        ("antenatal_postnatal", "Antenatal and postnatal care support", "ప్రసవ పూర్వ, ప్రసవానంతర సంరక్షణ సహాయం"),
        ("growth_monitoring", "Child growth monitoring", "పిల్లల ఎదుగుదల పర్యవేక్షణ"),
        ("immunization_followup", "Immunization follow-up", "టీకాల తదుపరి పర్యవేక్షణ"),
        ("nutrition_demo", "Nutrition demonstration", "పోషకాహార ప్రదర్శన"),
        ("record_reporting", "Record-keeping and reporting", "రికార్డులు మరియు నివేదికలు"),
        ("first_aid", "First aid", "ప్రథమ చికిత్స"),
        ("community_mobilisation", "Community mobilisation", "సమాజ సమీకరణ"),
    ],
    "auto_cab_drivers": [
        ("vehicle_maintenance", "Vehicle maintenance and minor repair", "వాహన నిర్వహణ మరియు చిన్న మరమ్మతులు"),
        ("safe_driving", "Safe and defensive driving", "సురక్షిత డ్రైవింగ్"),
        ("route_navigation", "Route navigation (app and local knowledge)", "మార్గనిర్దేశం (యాప్ మరియు స్థానిక పరిజ్ఞానం)"),
        ("customer_service", "Customer service", "కస్టమర్ సేవ"),
        ("vehicle_documentation", "Vehicle documentation handling", "వాహన పత్రాల నిర్వహణ"),
        ("app_tech_use", "App and GPS technology use", "యాప్ మరియు GPS సాంకేతికత వాడకం"),
    ],
    "banking_finance": [
        ("cash_reconciliation", "Cash handling and reconciliation", "నగదు నిర్వహణ మరియు సరిపోలిక"),
        ("loan_appraisal", "Loan appraisal and documentation", "రుణ మదింపు మరియు పత్రాలు"),
        ("kyc_verification", "Customer KYC verification", "కస్టమర్ KYC ధృవీకరణ"),
        ("digital_banking_assist", "Digital banking or app assistance", "డిజిటల్ బ్యాంకింగ్ / యాప్ సహాయం"),
        ("recovery_followup", "Recovery and follow-up", "వసూలు మరియు తదుపరి చర్యలు"),
        ("basic_accounting", "Basic accounting", "ప్రాథమిక అకౌంటింగ్"),
        ("shg_loan_facilitation", "SHG or group-loan facilitation", "SHG / గ్రూప్ రుణాల సౌకర్యం"),
    ],
    "bureaucrats": [
        ("file_noting", "File noting and documentation", "ఫైల్ నోటింగ్ మరియు పత్రాలు"),
        ("grievance_handling", "Public grievance handling", "ప్రజా ఫిర్యాదుల పరిష్కారం"),
        ("scheme_implementation", "Scheme implementation", "పథకాల అమలు"),
        ("budget_accounts", "Budget and account management", "బడ్జెట్ మరియు ఖాతాల నిర్వహణ"),
        ("inter_dept_coordination", "Coordination across departments", "శాఖల మధ్య సమన్వయం"),
        ("egovernance_tools", "Digital governance tools (e-office, portals)", "డిజిటల్ గవర్నెన్స్ టూల్స్ (ఈ-ఆఫీస్, పోర్టల్స్)"),
    ],
    "cashew": [
        ("nut_sorting_grading", "Nut sorting and grading", "గింజల సార్టింగ్ మరియు గ్రేడింగ్"),
        ("roasting_processing", "Roasting or processing operation", "వేయించడం / ప్రాసెసింగ్ నిర్వహణ"),
        ("kernel_extraction", "Kernel extraction", "గింజ తీయడం"),
        ("quality_control", "Quality control", "నాణ్యత నియంత్రణ"),
        ("machinery_operation_cashew", "Processing machinery operation", "ప్రాసెసింగ్ యంత్రాల నిర్వహణ"),
        ("packaging", "Packaging", "ప్యాకేజింగ్"),
    ],
    "chartered_accountants": [
        ("tax_filing", "Tax filing (GST / Income Tax)", "పన్ను దాఖలు (GST / ఆదాయపు పన్ను)"),
        ("audit_compliance", "Audit and compliance", "ఆడిట్ మరియు వర్తింపు"),
        ("bookkeeping_software", "Bookkeeping and accounting software", "బుక్‌కీపింగ్ మరియు అకౌంటింగ్ సాఫ్ట్‌వేర్"),
        ("financial_statements", "Financial statement preparation", "ఆర్థిక నివేదికల తయారీ"),
        ("advisory_consulting", "Advisory or consulting", "సలహా సేవలు"),
        ("digital_filing_portals", "Digital filing portals", "డిజిటల్ ఫైలింగ్ పోర్టల్స్"),
    ],
    "coffee_plantations": [
        ("pruning_shade", "Pruning and shade management", "కత్తిరింపు మరియు నీడ నిర్వహణ"),
        ("pulping_processing", "Pulping and processing", "పల్పింగ్ మరియు ప్రాసెసింగ్"),
        ("drying_grading", "Drying and grading", "ఎండబెట్టడం మరియు గ్రేడింగ్"),
        ("pest_disease_control", "Pest and disease control", "చీడపీడల నియంత్రణ"),
        ("organic_cultivation", "Organic cultivation methods", "సేంద్రియ సాగు పద్ధతులు"),
        ("harvesting_technique", "Harvesting techniques", "కోత పద్ధతులు"),
    ],
    "daily_wage_mgnrega_jaljeevan": [
        ("masonry", "Masonry or construction work", "మేస్త్రి / నిర్మాణ పని"),
        ("digging_earthwork", "Digging and earthwork", "తవ్వకం మరియు మట్టి పని"),
        ("plumbing_pipeline", "Plumbing or pipeline laying", "ప్లంబింగ్ లేదా పైప్‌లైన్ వేయడం"),
        ("carpentry", "Carpentry", "వడ్రంగం"),
        ("material_handling", "Material handling", "సామగ్రి నిర్వహణ"),
        ("basic_tool_operation", "Basic tool operation", "ప్రాథమిక పనిముట్ల వాడకం"),
    ],
    "ex_defence_staff": [
        ("security_vigilance", "Security and vigilance", "భద్రత మరియు నిఘా"),
        ("discipline_leadership", "Discipline and team leadership", "క్రమశిక్షణ మరియు బృంద నాయకత్వం"),
        ("heavy_vehicle_driving", "Heavy vehicle driving", "భారీ వాహనాల డ్రైవింగ్"),
        ("first_aid_emergency", "First aid or emergency response", "ప్రథమ చికిత్స / అత్యవసర స్పందన"),
        ("trade_skill_from_service", "Technical or trade skill from service", "సేవలో నేర్చుకున్న సాంకేతిక నైపుణ్యం"),
        ("training_mentoring", "Training or mentoring others", "ఇతరులకు శిక్షణ / మార్గదర్శకత్వం"),
    ],
    "govt_employees_contract": [
        ("file_processing", "File processing and documentation", "ఫైల్ ప్రాసెసింగ్ మరియు పత్రాలు"),
        ("public_service_delivery", "Public service delivery", "ప్రజా సేవల అందజేత"),
        ("computer_digital_skills", "Computer and digital skills", "కంప్యూటర్ మరియు డిజిటల్ నైపుణ్యాలు"),
        ("record_maintenance", "Record maintenance", "రికార్డుల నిర్వహణ"),
        ("dept_coordination", "Coordination with departments", "శాఖలతో సమన్వయం"),
    ],
    "homemakers": [
        ("cooking_preservation", "Cooking and food preservation", "వంట మరియు ఆహార భద్రపరచడం"),
        ("tailoring_embroidery", "Tailoring and embroidery", "కుట్టు మరియు ఎంబ్రాయిడరీ"),
        ("household_budgeting", "Household budgeting", "ఇంటి బడ్జెట్ నిర్వహణ"),
        ("childcare_eldercare", "Childcare and eldercare", "పిల్లలు మరియు వృద్ధుల సంరక్షణ"),
        ("kitchen_gardening", "Kitchen gardening", "ఇంటి పెరటి తోట"),
        ("handicraft_skill", "Handicraft or handloom-adjacent skill", "హస్తకళ లేదా చేనేత అనుబంధ నైపుణ్యం"),
    ],
    "hospitality_tourism": [
        ("cooking_food_prep", "Cooking or food preparation", "వంట లేదా ఆహార తయారీ"),
        ("housekeeping", "Housekeeping", "హౌస్‌కీపింగ్"),
        ("guest_service", "Guest service and communication", "అతిథుల సేవ మరియు సంభాషణ"),
        ("local_guiding", "Local guiding or area knowledge", "స్థానిక గైడింగ్ / ప్రాంత పరిజ్ఞానం"),
        ("billing_reservations", "Billing and reservations", "బిల్లింగ్ మరియు రిజర్వేషన్లు"),
        ("basic_language_skills", "Basic Hindi/English communication", "ప్రాథమిక హిందీ/ఇంగ్లీష్ సంభాషణ"),
    ],
    "it_corporate_management": [
        ("programming_coding", "Programming or coding", "ప్రోగ్రామింగ్"),
        ("data_analysis", "Data analysis", "డేటా విశ్లేషణ"),
        ("project_team_management", "Project or team management", "ప్రాజెక్ట్ / బృంద నిర్వహణ"),
        ("digital_marketing_tools", "Digital marketing tools", "డిజిటల్ మార్కెటింగ్ టూల్స్"),
        ("client_communication", "Client communication", "క్లయింట్ సంభాషణ"),
        ("cloud_software_tools", "Cloud or software tools", "క్లౌడ్ / సాఫ్ట్‌వేర్ టూల్స్"),
    ],
    "jaggery": [
        ("cane_crushing", "Cane crushing and juice extraction", "చెరకు తొక్కడం మరియు రసం తీయడం"),
        ("boiling_concentration", "Boiling and concentration control", "మరిగించడం మరియు గాఢత నియంత్రణ"),
        ("mould_setting", "Mould-setting and shaping", "అచ్చు వేయడం మరియు ఆకృతి"),
        ("grade_assessment", "Quality or grade assessment", "నాణ్యత / గ్రేడ్ అంచనా"),
        ("furnace_management", "Fuel and furnace management", "ఇంధనం మరియు బట్టీ నిర్వహణ"),
    ],
    "lawyers_advocates": [
        ("case_research_drafting", "Case research and drafting", "కేసు పరిశోధన మరియు దస్తావేజు రచన"),
        ("court_representation", "Court representation and argumentation", "కోర్టు ప్రాతినిధ్యం మరియు వాదన"),
        ("client_consultation", "Client consultation", "క్లయింట్ సంప్రదింపులు"),
        ("documentation_registration", "Documentation and registration work", "పత్రాలు మరియు రిజిస్ట్రేషన్ పని"),
        ("mediation_adr", "Mediation or ADR facilitation", "మధ్యవర్తిత్వం / ADR సౌకర్యం"),
    ],
    "manufacturing_msme": [
        ("machine_operation_mfg", "Machine operation", "యంత్ర నిర్వహణ"),
        ("quality_inspection", "Quality control or inspection", "నాణ్యత నియంత్రణ / తనిఖీ"),
        ("maintenance_repair", "Maintenance and repair", "నిర్వహణ మరియు మరమ్మతు"),
        ("production_planning", "Production planning", "ఉత్పత్తి ప్రణాళిక"),
        ("safety_procedures", "Safety procedures", "భద్రతా విధానాలు"),
        ("inventory_management", "Inventory management", "ఇన్వెంటరీ నిర్వహణ"),
    ],
    "marine_fisheries": [
        ("net_casting_mending", "Net casting and mending", "వల వేయడం మరియు బాగు చేయడం"),
        ("boat_operation", "Boat operation and navigation", "పడవ నిర్వహణ మరియు నావిగేషన్"),
        ("fish_sorting_grading", "Fish sorting and grading", "చేపల సార్టింగ్ మరియు గ్రేడింగ్"),
        ("engine_maintenance", "Engine maintenance", "ఇంజిన్ నిర్వహణ"),
        ("ice_coldchain", "Ice or cold-chain handling", "ఐస్ / కోల్డ్-చెయిన్ నిర్వహణ"),
        ("species_identification", "Species identification", "చేప జాతుల గుర్తింపు"),
    ],
    "mechanics": [
        ("engine_diagnosis_repair", "Engine diagnosis and repair", "ఇంజిన్ నిర్ధారణ మరియు మరమ్మతు"),
        ("electrical_wiring_repair", "Electrical or wiring repair", "విద్యుత్ / వైరింగ్ మరమ్మతు"),
        ("welding_fabrication", "Welding and fabrication", "వెల్డింగ్ మరియు ఫ్యాబ్రికేషన్"),
        ("tyre_brake_service", "Tyre and brake service", "టైర్ మరియు బ్రేక్ సర్వీస్"),
        ("diagnostic_tools", "Use of diagnostic tools", "డయాగ్నస్టిక్ టూల్స్ వాడకం"),
    ],
    "medical_personnel": [
        ("clinical_examination", "Clinical examination and diagnosis", "క్లినికల్ పరీక్ష మరియు నిర్ధారణ"),
        ("patient_care_nursing", "Patient care and nursing procedures", "రోగి సంరక్షణ మరియు నర్సింగ్ విధానాలు"),
        ("medicine_dispensing", "Medicine dispensing", "మందుల పంపిణీ"),
        ("medical_record_keeping", "Record-keeping", "రికార్డుల నిర్వహణ"),
        ("emergency_response", "Emergency or first response", "అత్యవసర స్పందన"),
        ("medical_equipment_use", "Use of medical equipment", "వైద్య పరికరాల వాడకం"),
    ],
    "mining": [
        ("drilling_blasting", "Drilling and blasting", "డ్రిల్లింగ్ మరియు బ్లాస్టింగ్"),
        ("equipment_operation_mining", "Machine or equipment operation", "యంత్రం / పరికరాల నిర్వహణ"),
        ("safety_compliance", "Safety procedure compliance", "భద్రతా విధాన వర్తింపు"),
        ("material_loading_transport", "Material loading and transport", "సామగ్రి లోడింగ్ మరియు రవాణా"),
        ("site_survey_assist", "Site survey assistance", "సైట్ సర్వే సహాయం"),
    ],
    "ngo_shg": [
        ("group_formation", "Group formation and facilitation", "గ్రూప్ ఏర్పాటు మరియు సౌకర్యం"),
        ("shg_bookkeeping", "Bookkeeping for SHGs", "SHGల కోసం బుక్‌కీపింగ్"),
        ("training_capacity_building", "Training and capacity building", "శిక్షణ మరియు సామర్థ్య నిర్మాణం"),
        ("proposal_reporting", "Proposal writing or reporting", "ప్రపోజల్ రచన / నివేదికలు"),
        ("community_mobilisation_ngo", "Community mobilisation", "సమాజ సమీకరణ"),
        ("monitoring_documentation", "Monitoring and documentation", "పర్యవేక్షణ మరియు డాక్యుమెంటేషన్"),
    ],
    "other_unlisted": [
        ("literacy_numeracy_use", "Basic literacy or numeracy use in work", "పనిలో ప్రాథమిక చదువు / లెక్కల వాడకం"),
        ("customer_public_dealing", "Customer or public dealing", "కస్టమర్ / ప్రజలతో వ్యవహారం"),
        ("tool_equipment_use", "Tool or equipment use specific to the work", "పనికి సంబంధించిన పరికరాల వాడకం"),
        ("record_keeping_other", "Record-keeping", "రికార్డుల నిర్వహణ"),
    ],
    "police": [
        ("patrolling_surveillance", "Patrolling and surveillance", "పెట్రోలింగ్ మరియు నిఘా"),
        ("law_order_management", "Law and order management", "శాంతిభద్రతల నిర్వహణ"),
        ("investigation_evidence", "Investigation and evidence handling", "దర్యాప్తు మరియు సాక్ష్యాధారాల నిర్వహణ"),
        ("public_complaint_handling", "Public interaction and complaint handling", "ప్రజలతో వ్యవహారం మరియు ఫిర్యాదుల పరిష్కారం"),
        ("traffic_management", "Traffic management", "ట్రాఫిక్ నిర్వహణ"),
        ("comms_tech_systems", "Use of communication or technology systems", "కమ్యూనికేషన్ / సాంకేతిక వ్యవస్థల వాడకం"),
    ],
    "political_workers": [
        ("public_speaking_mobilisation", "Public speaking and mobilisation", "బహిరంగ ప్రసంగం మరియు సమీకరణ"),
        ("event_campaign_organising", "Event or campaign organising", "కార్యక్రమం / ప్రచార నిర్వహణ"),
        ("grievance_coordination", "Grievance redressal coordination", "ఫిర్యాదుల పరిష్కార సమన్వయం"),
        ("social_media_outreach", "Social media or digital outreach", "సోషల్ మీడియా / డిజిటల్ అవుట్రీచ్"),
        ("community_liaison", "Community liaison", "సామాజిక సంధానకర్త"),
    ],
    "quick_commerce": [
        ("two_wheeler_riding", "Two-wheeler riding", "ద్విచక్ర వాహన నడపడం"),
        ("app_navigation_use", "App or navigation use", "యాప్ / నావిగేషన్ వాడకం"),
        ("delivery_time_management", "Time management for deliveries", "డెలివరీల కోసం సమయ నిర్వహణ"),
        ("customer_handling_qc", "Customer handling", "కస్టమర్ నిర్వహణ"),
        ("order_package_handling", "Order or package handling", "ఆర్డర్ / ప్యాకేజీ నిర్వహణ"),
    ],
    "ration_dealers": [
        ("stock_inventory", "Stock or inventory management", "స్టాక్ / ఇన్వెంటరీ నిర్వహణ"),
        ("weighing_measurement", "Weighing and measurement accuracy", "తూకం మరియు కొలత ఖచ్చితత్వం"),
        ("digital_record_epos", "Record-keeping (ePOS or digital)", "రికార్డులు (ePOS / డిజిటల్)"),
        ("customer_service_rd", "Customer service", "కస్టమర్ సేవ"),
        ("biometric_verification", "Biometric or digital verification handling", "బయోమెట్రిక్ / డిజిటల్ ధృవీకరణ నిర్వహణ"),
    ],
    "real_estate": [
        ("property_valuation", "Property valuation", "ఆస్తి విలువ అంచనా"),
        ("documentation_registration_re", "Documentation and registration process knowledge", "పత్రాలు మరియు రిజిస్ట్రేషన్ ప్రక్రియ పరిజ్ఞానం"),
        ("client_negotiation", "Client negotiation", "క్లయింట్ చర్చలు"),
        ("property_marketing", "Marketing or advertising a property", "ఆస్తి మార్కెటింగ్ / ప్రకటన"),
        ("legal_paperwork", "Legal paperwork handling", "న్యాయపరమైన పత్రాల నిర్వహణ"),
    ],
    "religious_leaders": [
        ("ritual_ceremony_conduct", "Religious ceremony or ritual conduct", "మతపరమైన కార్యక్రమాలు / ఆచారాల నిర్వహణ"),
        ("public_speaking_preaching", "Public speaking or preaching", "బహిరంగ ప్రసంగం / బోధన"),
        ("community_counselling", "Community counselling", "సమాజ సలహా"),
        ("event_organisation_rel", "Event organisation", "కార్యక్రమ నిర్వహణ"),
        ("institution_accounts", "Institution or accounts management", "సంస్థ / ఖాతాల నిర్వహణ"),
    ],
    "restaurant_workers": [
        ("cooking_food_prep_rest", "Cooking or food preparation", "వంట లేదా ఆహార తయారీ"),
        ("food_safety_hygiene", "Food safety and hygiene practices", "ఆహార భద్రత మరియు పరిశుభ్రత పద్ధతులు"),
        ("customer_service_rest", "Customer service", "కస్టమర్ సేవ"),
        ("billing_order_management", "Billing or order management", "బిల్లింగ్ / ఆర్డర్ నిర్వహణ"),
        ("kitchen_equipment_operation", "Kitchen equipment operation", "వంటగది పరికరాల నిర్వహణ"),
    ],
    "retired_persons": [
        ("former_occupation_skill", "Skill from former occupation (advisory or mentoring use)", "పూర్వ వృత్తి నైపుణ్యం (సలహా / మార్గదర్శకత్వం)"),
        ("basic_digital_mobile_use", "Basic digital or mobile phone use", "ప్రాథమిక డిజిటల్ / మొబైల్ వాడకం"),
        ("financial_pension_mgmt", "Financial or pension management", "ఆర్థిక / పింఛను నిర్వహణ"),
        ("community_social_work", "Community or social work involvement", "సమాజ / సామాజిక సేవలో పాల్గొనడం"),
    ],
    "rtc_workers": [
        ("heavy_vehicle_driving_rtc", "Heavy vehicle driving", "భారీ వాహనాల డ్రైవింగ్"),
        ("vehicle_maintenance_checks", "Vehicle maintenance checks", "వాహన నిర్వహణ తనిఖీలు"),
        ("ticketing_conducting", "Ticketing or conducting", "టికెటింగ్ / కండక్టింగ్"),
        ("route_knowledge", "Route knowledge", "మార్గ పరిజ్ఞానం"),
        ("passenger_safety", "Passenger safety management", "ప్రయాణికుల భద్రత నిర్వహణ"),
    ],
    "self_employed_entrepreneurs": [
        ("business_planning_costing", "Business planning and costing", "వ్యాపార ప్రణాళిక మరియు ధర నిర్ణయం"),
        ("marketing_sales", "Marketing and sales", "మార్కెటింగ్ మరియు అమ్మకాలు"),
        ("inventory_stock_mgmt", "Inventory or stock management", "ఇన్వెంటరీ / స్టాక్ నిర్వహణ"),
        ("customer_relationship", "Customer relationship handling", "కస్టమర్ సంబంధాల నిర్వహణ"),
        ("basic_accounting_se", "Basic accounting", "ప్రాథమిక అకౌంటింగ్"),
        ("digital_payment_handling", "Digital payment handling", "డిజిటల్ చెల్లింపుల నిర్వహణ"),
    ],
    "social_media_marketing": [
        ("content_creation", "Content creation (photo, video, text)", "కంటెంట్ తయారీ (ఫోటో, వీడియో, టెక్స్ట్)"),
        ("platform_management", "Social media platform management", "సోషల్ మీడియా ప్లాట్‌ఫామ్ నిర్వహణ"),
        ("graphic_design_editing", "Basic graphic design or editing", "ప్రాథమిక గ్రాఫిక్ డిజైన్ / ఎడిటింగ్"),
        ("analytics_engagement", "Analytics and engagement tracking", "అనలిటిక్స్ మరియు ఎంగేజ్‌మెంట్ ట్రాకింగ్"),
        ("client_communication_smm", "Client communication", "క్లయింట్ సంభాషణ"),
    ],
    "students": [
        ("computer_digital_literacy", "Computer or digital literacy", "కంప్యూటర్ / డిజిటల్ అక్షరాస్యత"),
        ("communication_language", "Communication or language skills", "సంభాషణ / భాషా నైపుణ్యాలు"),
        ("subject_technical_skill", "Subject-specific technical skill (lab, workshop, etc.)", "సబ్జెక్టు-నిర్దిష్ట సాంకేతిక నైపుణ్యం (ల్యాబ్, వర్క్‌షాప్ మొదలైనవి)"),
        ("part_time_work_skill", "A part-time work skill", "పార్ట్-టైమ్ పని నైపుణ్యం"),
    ],
    "tailors_garment": [
        ("cutting_stitching", "Cutting and stitching", "కత్తిరింపు మరియు కుట్టు"),
        ("embroidery_design_tg", "Embroidery or design work", "ఎంబ్రాయిడరీ / డిజైన్ పని"),
        ("measurement_taking", "Measurement taking", "కొలతలు తీసుకోవడం"),
        ("machine_operation_tg", "Sewing or embroidery machine operation", "కుట్టు / ఎంబ్రాయిడరీ యంత్రాల నిర్వహణ"),
        ("alteration_work", "Alteration work", "మార్పులు చేసే పని"),
    ],
    "teachers": [
        ("lesson_planning", "Lesson planning and delivery", "పాఠ ప్రణాళిక మరియు బోధన"),
        ("classroom_management", "Classroom management", "తరగతి గది నిర్వహణ"),
        ("student_assessment", "Student assessment", "విద్యార్థుల మూల్యాంకనం"),
        ("digital_teaching_tools", "Use of digital teaching tools", "డిజిటల్ బోధన సాధనాల వాడకం"),
        ("subject_expertise", "Subject-specific expertise", "సబ్జెక్టు-నిర్దిష్ట నైపుణ్యం"),
        ("remedial_special_needs", "Remedial or special-needs teaching", "రెమెడియల్ / ప్రత్యేక అవసరాల బోధన"),
    ],
    "toddy_plantation": [
        ("tree_climbing_tapping", "Tree climbing and tapping", "చెట్టు ఎక్కడం మరియు గీత పని"),
        ("pot_collection_mgmt", "Pot or collection management", "కుండ / సేకరణ నిర్వహణ"),
        ("fermentation_control", "Fermentation control", "కిణ్వ ప్రక్రియ నియంత్రణ"),
        ("tree_maintenance", "Tree maintenance or pruning", "చెట్ల నిర్వహణ / కత్తిరింపు"),
        ("safety_equipment_use", "Safety equipment use", "భద్రతా పరికరాల వాడకం"),
    ],
    "transgender": [
        ("cooking_skill_trg", "Cooking", "వంట"),
        ("tailoring_skill_trg", "Tailoring", "కుట్టు పని"),
        ("beautician_grooming", "Beautician or grooming services", "బ్యూటీషియన్ సేవలు"),
        ("performing_arts", "Performing arts (dance, music)", "ప్రదర్శన కళలు (నృత్యం, సంగీతం)"),
        ("vending_trading", "Vending or small trading", "వీధి వ్యాపారం / చిన్న వ్యాపారం"),
        ("peer_counselling", "Peer counselling or support work", "తోటివారి సలహా / మద్దతు పని"),
    ],
    "transport_business": [
        ("fleet_management", "Vehicle fleet management", "వాహన సముదాయ నిర్వహణ"),
        ("driving_various_vehicles", "Driving (various vehicle types)", "వివిధ రకాల వాహనాలు నడపడం"),
        ("logistics_route_planning", "Logistics or route planning", "లాజిస్టిక్స్ / మార్గ ప్రణాళిక"),
        ("vehicle_maintenance_oversight", "Vehicle maintenance oversight", "వాహన నిర్వహణ పర్యవేక్షణ"),
        ("documentation_permit", "Documentation or permit handling", "పత్రాలు / పర్మిట్ నిర్వహణ"),
    ],
    "unemployed_jobseekers": [
        ("basic_digital_literacy_uj", "Basic digital or computer literacy", "ప్రాథమిక డిజిటల్ / కంప్యూటర్ అక్షరాస్యత"),
        ("communication_skill_uj", "Communication skills", "సంభాషణ నైపుణ్యాలు"),
        ("informal_trade_skill", "A trade skill learned informally", "అనధికారికంగా నేర్చుకున్న వృత్తి నైపుణ్యం"),
        ("resume_application_prep", "Resume or application preparation", "రెజ్యూమె / దరఖాస్తు తయారీ"),
    ],
}
for occ_code, skills in B09_SKILLS.items():
    for code, en, te in skills:
        choice("b09_skills", f"{occ_code}_{code}", en, te, occ_filter=occ_code)
    choice("b09_skills", f"{occ_code}_none", "None", "ఏదీ లేదు", occ_filter=occ_code)

choice("employer_type", "govt_dept_company", "Government department or government company", "ప్రభుత్వ విభాగం లేదా ప్రభుత్వ సంస్థ")
choice("employer_type", "private_company_shop", "Private company or shop", "ప్రైవేటు కంపెనీ లేదా దుకాణం")
choice("employer_type", "contractor_mestri", "A contractor or mestri", "కాంట్రాక్టర్ లేదా మేస్త్రి")
choice("employer_type", "household_farmer", "A household or a farmer", "ఒక ఇంటివారు లేదా రైతు")
choice("employer_type", "platform", "A platform (app-based company)", "ఒక ప్లాట్‌ఫామ్ (యాప్ ఆధారిత సంస్థ)")
choice("employer_type", "govt_scheme", "A government work scheme (for example MGNREGA)", "ప్రభుత్వ పని పథకం (ఉదాహరణకు MGNREGA)")
choice("employer_type", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("pns_choice", "enter_amount", "Enter the amount", "మొత్తాన్ని నమోదు చేయండి")
choice("pns_choice", "pns", "Prefer not to say", "చెప్పదలచుకోలేదు")

choice("skill_need", "technical_craft", "Technical or craft skill", "సాంకేతిక లేదా హస్తకళా నైపుణ్యం")
choice("skill_need", "business_finance", "Business or financial management", "వ్యాపార లేదా ఆర్థిక నిర్వహణ")
choice("skill_need", "digital_computer", "Digital or computer skill", "డిజిటల్ లేదా కంప్యూటర్ నైపుణ్యం")
choice("skill_need", "marketing_sales", "Marketing or sales skill", "మార్కెటింగ్ లేదా అమ్మకాల నైపుణ్యం")
choice("skill_need", "language_communication", "Language or communication skill", "భాష లేదా భావ వ్యక్తీకరణ నైపుణ్యం")
choice("skill_need", "no_training_needed", "No training needed", "శిక్షణ అవసరం లేదు")
choice("skill_need", "other", "Other", "ఇతర")

choice("pay_unit", "per_day", "Per day", "రోజుకు")
choice("pay_unit", "per_month", "Per month", "నెలకు")
choice("pay_unit", "per_piece_task", "Per piece or task", "పని/ముక్కకు")

# ---- Weavers-specific choices ----
choice("wv_work_pay_arrangement", "buy_sell_myself", "I buy yarn and sell the cloth myself", "నేను దారం కొని, వస్త్రాన్ని నేనే అమ్ముకుంటాను")
choice("wv_work_pay_arrangement", "master_piece_rate", "I weave for a master weaver and am paid per piece or metre", "నేను మేస్త్రి నేతకారుడి కోసం నేస్తాను, ముక్క లేదా మీటరుకు వేతనం పొందుతాను")
choice("wv_work_pay_arrangement", "others_loom_wage", "I weave on someone else's loom and am paid daily or monthly", "నేను వేరొకరి మగ్గంపై నేస్తాను, రోజువారీ లేదా నెలవారీ వేతనం పొందుతాను")
choice("wv_work_pay_arrangement", "cooperative", "I weave through a cooperative society", "సహకార సంఘం ద్వారా నేస్తాను")
choice("wv_work_pay_arrangement", "individual_orders", "I weave for individual customers on order", "వ్యక్తిగత కస్టమర్ల ఆర్డర్ల కోసం నేస్తాను")
choice("wv_work_pay_arrangement", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_loom_type_owner", "own_pit_frame", "Own pit or frame handloom", "సొంత పిట్ లేదా ఫ్రేమ్ చేనేత మగ్గం")
choice("wv_loom_type_owner", "own_jacquard_dobby", "Own jacquard or dobby handloom", "సొంత జాకార్డ్ లేదా డాబీ చేనేత మగ్గం")
choice("wv_loom_type_owner", "own_powerloom", "Own powerloom", "సొంత పవర్‌లూమ్")
choice("wv_loom_type_owner", "master_weaver_loom", "Master weaver's loom", "మేస్త్రి నేతకారుడి మగ్గం")
choice("wv_loom_type_owner", "cooperative_loom", "Cooperative society's loom", "సహకార సంఘం మగ్గం")
choice("wv_loom_type_owner", "rented_loom", "Rented loom", "అద్దె మగ్గం")
choice("wv_loom_type_owner", "shared_loom", "Shared loom", "భాగస్వామ్య మగ్గం")
choice("wv_loom_type_owner", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_unit", "pieces", "Pieces", "ముక్కలు")
choice("wv_unit", "metres", "Metres", "మీటర్లు")

choice("wv_cloth_buyer", "master_advance_tied", "A master weaver who gives yarn or an advance on condition cloth only to him", "దారం లేదా అడ్వాన్సు ఇచ్చి, వస్త్రం తనకే ఇవ్వాలనే షరతుతో ఉన్న మేస్త్రి నేతకారుడు")
choice("wv_cloth_buyer", "master_wholesaler_rate", "A master weaver or wholesaler, at his rate", "మేస్త్రి నేతకారుడు లేదా టోకు వ్యాపారి, అతని రేటుకు")
choice("wv_cloth_buyer", "apco_cooperative", "APCO or a cooperative society, at a fixed rate", "APCO లేదా సహకార సంఘం, నిర్ణీత రేటుకు")
choice("wv_cloth_buyer", "local_trader", "A local trader or cloth shop, at their price", "స్థానిక వ్యాపారి లేదా వస్త్ర దుకాణం, వారి ధరకు")
choice("wv_cloth_buyer", "direct_customers", "Direct customers, at my price", "ప్రత్యక్ష కస్టమర్లు, నా ధరకు")
choice("wv_cloth_buyer", "exhibition_market", "An exhibition or local market", "ఎగ్జిబిషన్ లేదా స్థానిక సంత")
choice("wv_cloth_buyer", "online_buyer", "An online buyer", "ఆన్‌లైన్ కొనుగోలుదారు")
choice("wv_cloth_buyer", "na_wage_worker", "Not applicable, I work for wages", "వర్తించదు, నేను వేతనం కోసం పనిచేస్తాను")
choice("wv_cloth_buyer", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_extra_work", "nothing_extra", "Nothing extra", "అదనంగా ఏమీ లేదు")
choice("wv_extra_work", "washing_finishing", "Washing or finishing", "ఉతకడం లేదా ఫినిషింగ్")
choice("wv_extra_work", "dyeing_printing", "Dyeing or printing", "రంగులు వేయడం లేదా ప్రింటింగ్")
choice("wv_extra_work", "embroidery_designs", "Embroidery or extra designs", "ఎంబ్రాయిడరీ లేదా అదనపు డిజైన్లు")
choice("wv_extra_work", "stitching_garments", "Stitching into garments", "దుస్తులుగా కుట్టడం")
choice("wv_extra_work", "branding_packing", "Branding, packing or labelling (for example the Handloom Mark)", "బ్రాండింగ్, ప్యాకింగ్ లేదా లేబులింగ్ (ఉదా. హ్యాండ్లూమ్ మార్క్)")
choice("wv_extra_work", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_documents_held", "weaver_id_pehchan", "Weaver ID card (Pehchan card)", "చేనేత గుర్తింపు కార్డు (పెహచాన్ కార్డు)")
choice("wv_documents_held", "cooperative_membership", "Cooperative society membership", "సహకార సంఘం సభ్యత్వం")
choice("wv_documents_held", "udyam_registration", "Udyam registration", "ఉద్యమ్ నమోదు")
choice("wv_documents_held", "handloom_mark_gi", "Handloom Mark or GI tag for my product", "హ్యాండ్లూమ్ మార్క్ లేదా GI టాగ్")
choice("wv_documents_held", "none", "None of these", "వీటిలో ఏదీ లేదు")
choice("wv_documents_held", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_infra_usable", "work_shed", "Proper work shed for the loom", "మగ్గం కోసం సరైన పని షెడ్")
choice("wv_infra_usable", "steady_electricity", "Steady electricity", "నిలకడైన విద్యుత్")
choice("wv_infra_usable", "good_lighting", "Good lighting", "మంచి వెలుతురు")
choice("wv_infra_usable", "yarn_depot_nearby", "Yarn depot or seller nearby", "సమీపంలో దారం డిపో లేదా అమ్మకందారు")
choice("wv_infra_usable", "dyeing_unit_nearby", "Dyeing unit nearby", "సమీపంలో డైయింగ్ యూనిట్")
choice("wv_infra_usable", "common_facility_centre", "Common facility centre (warping, sizing, finishing)", "ఉమ్మడి సదుపాయ కేంద్రం (వార్పింగ్, సైజింగ్, ఫినిషింగ్)")
choice("wv_infra_usable", "safe_storage", "Safe storage for cloth", "వస్త్రం కోసం సురక్షిత నిల్వ")
choice("wv_infra_usable", "none", "None of these", "వీటిలో ఏదీ లేదు")
choice("wv_infra_usable", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_skills_self", "plain_weaving", "Plain weaving", "సాదా నేత")
choice("wv_skills_self", "jacquard_dobby_design", "Jacquard or dobby design weaving", "జాకార్డ్ లేదా డాబీ డిజైన్ నేత")
choice("wv_skills_self", "extra_weft_border", "Extra-weft or border designs", "ఎక్స్ట్రా-వెఫ్ట్ లేదా అంచు డిజైన్లు")
choice("wv_skills_self", "hand_spinning", "Hand spinning (charkha)", "చేతి వడకడం (చరఖా)")
choice("wv_skills_self", "dyeing", "Dyeing", "రంగులు వేయడం")
choice("wv_skills_self", "warping_sizing", "Warping and sizing", "వార్పింగ్ మరియు సైజింగ్")
choice("wv_skills_self", "computer_design", "Computer design for weaving", "నేత కోసం కంప్యూటర్ డిజైన్")
choice("wv_skills_self", "none", "None of these", "వీటిలో ఏదీ లేదు")
choice("wv_skills_self", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_govt_support_12m", "nethanna_sevalo", "Nethanna Sevalo (Rs.25,000 a year)", "నేతన్న సేవలో (సంవత్సరానికి రూ.25,000)")
choice("wv_govt_support_12m", "free_power", "Free power (200 units for handloom, 500 units for powerloom)", "ఉచిత విద్యుత్ (చేనేతకు 200 యూనిట్లు, పవర్‌లూమ్‌కు 500 యూనిట్లు)")
choice("wv_govt_support_12m", "ntr_bharosa_pension", "NTR Bharosa pension for weavers aged 50 and above (Rs.4,000 a month)", "NTR భరోసా పింఛను, 50 ఏళ్లు పైబడిన నేతకారులకు (నెలకు రూ.4,000)")
choice("wv_govt_support_12m", "yarn_subsidy", "Yarn subsidy", "దారం సబ్సిడీ")
choice("wv_govt_support_12m", "weaver_insurance", "Weaver insurance", "చేనేత బీమా")
choice("wv_govt_support_12m", "coop_mudra_loan", "Loan through the cooperative or Mudra", "సహకార సంఘం లేదా ముద్ర ద్వారా రుణం")
choice("wv_govt_support_12m", "applied_waiting", "Applied, still waiting", "దరఖాస్తు చేశాను, ఇంకా వేచి ఉన్నాను")
choice("wv_govt_support_12m", "aware_not_applied", "I know about these but did not apply", "వీటి గురించి తెలుసు కానీ దరఖాస్తు చేయలేదు")
choice("wv_govt_support_12m", "not_aware", "I did not know about any of these", "వీటి గురించి ఏమీ తెలియదు")
choice("wv_govt_support_12m", "other", "Other (specify)", "ఇతర (తెలపండి)")

choice("wv_work_incidents_12m", "eye_back_pain", "Eye or back pain that affected weaving", "నేత పనిని ప్రభావితం చేసిన కళ్ళు లేదా వీపు నొప్పి")
choice("wv_work_incidents_12m", "injury_got_help", "Injury while weaving or preparing yarn, got help", "నేత లేదా దారం తయారీలో గాయం, సహాయం పొందారు")
choice("wv_work_incidents_12m", "injury_no_help", "Injury while weaving or preparing yarn, no help", "నేత లేదా దారం తయారీలో గాయం, సహాయం పొందలేదు")
choice("wv_work_incidents_12m", "damage_compensated", "Loom or cloth damaged by rain, flood or fire, got compensation", "వర్షం, వరద లేదా అగ్ని వల్ల మగ్గం లేదా వస్త్రం దెబ్బతినడం, పరిహారం అందింది")
choice("wv_work_incidents_12m", "damage_not_compensated", "Loom or cloth damaged by rain, flood or fire, no compensation", "వర్షం, వరద లేదా అగ్ని వల్ల మగ్గం లేదా వస్త్రం దెబ్బతినడం, పరిహారం అందలేదు")
choice("wv_work_incidents_12m", "payment_not_received", "Payment for my cloth not received", "నా వస్త్రానికి చెల్లింపు అందలేదు")
choice("wv_work_incidents_12m", "none", "None of these", "వీటిలో ఏదీ లేదు")
choice("wv_work_incidents_12m", "other", "Other (specify)", "ఇతర (తెలపండి)")

# ---- Remaining 41 profession modules' choices ----
for _mod in _loaded_prof_modules:
    _mod.add_choices(choice)

# ---- Political-section choices (compressed, one question per theme) ----
priority_problem_list = [
    ("jobs_employment", "Jobs / Employment", "ఉద్యోగాలు / ఉపాధి"),
    ("cost_of_living", "Daily commodities price / Cost of living", "నిత్యావసర వస్తువుల ధరలు / జీవన వ్యయం"),
    ("education", "Education", "విద్య"),
    ("healthcare", "Healthcare (Government Hospital / PHC)", "ఆరోగ్య సేవలు (ప్రభుత్వ ఆసుపత్రి / PHC)"),
    ("drinking_water", "Drinking water", "తాగునీరు"),
    ("farming_support", "Farming / Agriculture and farm prices", "వ్యవసాయం మరియు పంట ధరలు"),
    ("roads_infra", "Roads & Infrastructure", "రోడ్లు మరియు మౌలిక సదుపాయాలు"),
    ("power_supply", "Power supply", "విద్యుత్ సరఫరా"),
    ("housing", "Housing", "గృహవసతి"),
    ("law_order", "Law and order", "శాంతిభద్రతలు"),
    ("welfare_schemes", "Welfare schemes", "సంక్షేమ పథకాలు"),
    ("industrial_dev", "Industrial development (even with some environmental impact)", "పారిశ్రామిక అభివృద్ధి (కొంత పర్యావరణ ప్రభావం ఉన్నా)"),
    ("paperwork_delays", "Paperwork and delays in offices", "కార్యాలయాల్లో కాగితాల పని, ఆలస్యాలు"),
    ("other", "Other (specify)", "ఇతర (తెలపండి)"),
]
for name, en, te in priority_problem_list:
    choice("priority_problem", name, en, te)

choice("responsible_party", "local_body", "Village / ward / municipality (local body)", "గ్రామం / వార్డు / మున్సిపాలిటీ (స్థానిక సంస్థ)")
choice("responsible_party", "state_govt", "State government", "రాష్ట్ర ప్రభుత్వం")
choice("responsible_party", "central_govt", "Central government", "కేంద్ర ప్రభుత్వం")
choice("responsible_party", "someone_else", "Someone else (private people, companies, society)", "వేరెవరో (ప్రైవేటు వ్యక్తులు, సంస్థలు, సమాజం)")
choice("responsible_party", "dont_know", "Don't know", "తెలియదు")

choice("trust_satisfaction", "a_lot", "A lot", "చాలా ఎక్కువ")
choice("trust_satisfaction", "some", "Some", "కొంత")
choice("trust_satisfaction", "little", "Little", "కొద్దిగా")
choice("trust_satisfaction", "none", "None", "అసలు లేదు")
choice("trust_satisfaction", "dont_know", "Don't know", "తెలియదు")

choice("scheme_awareness_funnel", "not_aware", "Not aware of any scheme I could apply for", "నేను దరఖాస్తు చేసుకోగల పథకం గురించి తెలియదు")
choice("scheme_awareness_funnel", "aware_not_applied", "Aware of a scheme, but have not applied", "పథకం గురించి తెలుసు, కానీ దరఖాస్తు చేయలేదు")
choice("scheme_awareness_funnel", "applied_not_received", "Applied, but have not received the benefit yet", "దరఖాస్తు చేశాను, కానీ ఇంకా ప్రయోజనం అందలేదు")
choice("scheme_awareness_funnel", "received", "Applied and received the benefit", "దరఖాస్తు చేసి ప్రయోజనం పొందాను")

choice("complaint_knowledge", "know_full_process", "Yes, I know the process", "అవును, పద్ధతి నాకు తెలుసు")
choice("complaint_knowledge", "know_where_not_process", "I know where to complain, but not the full process", "ఎక్కడ ఫిర్యాదు చేయాలో తెలుసు, పూర్తి పద్ధతి తెలియదు")
choice("complaint_knowledge", "heard_not_how", "I have heard about it, but do not know how", "విన్నాను, కానీ ఎలానో తెలియదు")
choice("complaint_knowledge", "no_idea", "No, I do not know the process", "లేదు, పద్ధతి నాకు తెలియదు")

choice("welfare_compare_govts", "better", "Better", "మెరుగైంది")
choice("welfare_compare_govts", "same", "Same", "యథాతథంగా ఉంది")
choice("welfare_compare_govts", "worse", "Worse", "తగ్గింది")
choice("welfare_compare_govts", "dont_know", "Don't Know", "తెలియదు")

choice("welfare_availed", "yes", "Yes", "అవును")
choice("welfare_availed", "no", "No", "లేదు")
choice("welfare_availed", "not_eligible", "Not eligible", "అర్హత లేదు")

choice("health_104_108", "known_used", "Yes, I know about them and have used them here", "అవును, తెలుసు మరియు ఇక్కడ వాడాను")
choice("health_104_108", "known_not_available", "Yes, I know about them, but not available/functional here", "అవును, తెలుసు, కానీ ఇక్కడ అందుబాటులో లేవు / పనిచేయడం లేదు")
choice("health_104_108", "known_not_used", "Yes, I know about them, but never needed to use them", "అవును, తెలుసు, కానీ వాడాల్సిన అవసరం రాలేదు")
choice("health_104_108", "never_heard", "No, I have never heard of these services", "లేదు, ఈ సేవల గురించి ఎప్పుడూ వినలేదు")

choice("complaint_channel", "village_secretariat", "Visit the Village/Ward Secretariat", "గ్రామ/వార్డు సచివాలయానికి వెళ్లడం")
choice("complaint_channel", "panchayat_municipality", "Visit the Gram Panchayat or Municipality office", "గ్రామ పంచాయతీ లేదా మున్సిపాలిటీ కార్యాలయానికి వెళ్లడం")
choice("complaint_channel", "mandal_office", "Visit the Mandal office (MRO/MPDO)", "మండల కార్యాలయానికి వెళ్లడం (MRO/MPDO)")
choice("complaint_channel", "website_app", "Submit through a government website or mobile app", "ప్రభుత్వ వెబ్‌సైట్ లేదా యాప్ ద్వారా సమర్పించడం")
choice("complaint_channel", "helpline", "Call a government helpline", "ప్రభుత్వ హెల్ప్‌లైన్‌కు కాల్ చేయడం")
choice("complaint_channel", "local_rep", "Approach the Sarpanch, Ward Member or local representative", "సర్పంచ్, వార్డు సభ్యుడు లేదా స్థానిక ప్రతినిధిని సంప్రదించడం")
choice("complaint_channel", "other", "Other (specify)", "ఇతర (తెలపండి)")
choice("complaint_channel", "dont_know_how", "I do not know how to submit a complaint", "ఫిర్యాదు ఎలా చేయాలో నాకు తెలియదు")

choice("complaint_satisfaction", "very_satisfied", "Very satisfied", "చాలా సంతృప్తిగా ఉన్నాను")
choice("complaint_satisfaction", "satisfied", "Satisfied", "సంతృప్తిగా ఉన్నాను")
choice("complaint_satisfaction", "neutral", "Neither satisfied nor dissatisfied", "సంతృప్తి, అసంతృప్తి రెండూ కాదు")
choice("complaint_satisfaction", "dissatisfied", "Dissatisfied", "అసంతృప్తిగా ఉన్నాను")
choice("complaint_satisfaction", "very_dissatisfied", "Very dissatisfied", "చాలా అసంతృప్తిగా ఉన్నాను")
choice("complaint_satisfaction", "not_submitted", "I have not submitted a complaint", "నేను ఫిర్యాదు చేయలేదు")
choice("complaint_satisfaction", "not_sure", "Not sure", "ఖచ్చితంగా తెలియదు")

choice("dev_env_priority", "dev_priority", "Developmental work must take priority", "అభివృద్ధి పనులకే ప్రాధాన్యత ఇవ్వాలి")
choice("dev_env_priority", "dev_with_conditions", "Development can proceed, but only under strict environmental conditions", "కఠినమైన పర్యావరణ షరతులతో అభివృద్ధి కొనసాగవచ్చు")
choice("dev_env_priority", "env_priority", "Environmental protection must take priority", "పర్యావరణ పరిరక్షణకే ప్రాధాన్యత ఇవ్వాలి")
choice("dev_env_priority", "balanced", "Both must be balanced equally", "రెండింటినీ సమానంగా సమతుల్యం చేయాలి")

choice("info_source", "tv", "Television", "టీవీ")
choice("info_source", "newspaper", "Newspaper", "వార్తాపత్రిక")
choice("info_source", "radio", "Radio", "రేడియో")
choice("info_source", "social_media", "Social media", "సోషల్ మీడియా")
choice("info_source", "word_of_mouth", "Word of mouth", "నోటిమాటగా")
choice("info_source", "none", "None of these", "వీటిలో ఏదీ లేదు")

choice("social_platform", "facebook", "Facebook", "ఫేస్‌బుక్")
choice("social_platform", "whatsapp", "WhatsApp", "వాట్సాప్")
choice("social_platform", "youtube", "YouTube", "యూట్యూబ్")
choice("social_platform", "instagram", "Instagram", "ఇన్‌స్టాగ్రామ్")
choice("social_platform", "x_twitter", "X (formerly Twitter)", "X (గతంలో ట్విట్టర్)")

choice("leader_quality", "honesty", "Honesty and integrity", "నిజాయితీ మరియు సచ్ఛీలత")
choice("leader_quality", "accessible", "Being easily accessible/meetable", "సులభంగా అందుబాటులో ఉండటం")
choice("leader_quality", "track_record", "Past work and performance track record", "గత పని, పనితీరు చరిత్ర")
choice("leader_quality", "personality_image", "Personality, image or reputation", "వ్యక్తిత్వం, ఇమేజ్ లేదా ఖ్యాతి")
choice("leader_quality", "education", "Educational qualifications", "విద్యార్హతలు")
choice("leader_quality", "party", "The political party represented", "ప్రాతినిధ్యం వహిస్తున్న రాజకీయ పార్టీ")
choice("leader_quality", "native_resident", "Being a native resident of your area", "మీ ప్రాంతానికి చెందినవారు అవడం")
choice("leader_quality", "woman", "Being a woman", "మహిళ అవడం")
choice("leader_quality", "caste", "Caste", "కులం")
choice("leader_quality", "religion", "Religion", "మతం")

choice("reservation_opinion", "increased", "Increased", "పెంచాలి")
choice("reservation_opinion", "decreased", "Decreased", "తగ్గించాలి")
choice("reservation_opinion", "same", "Kept exactly the same", "యథాతథంగా ఉంచాలి")
choice("reservation_opinion", "no_opinion", "No opinion / Don't know", "అభిప్రాయం లేదు / తెలియదు")

facilities_list = [
    ("cold_storage", "Cold storage or ice plant", "కోల్డ్ స్టోరేజ్ లేదా ఐస్ ప్లాంట్"),
    ("fish_landing", "Fish landing centre or jetty", "చేపల దిగుమతి కేంద్రం లేదా జెట్టీ"),
    ("cashew_unit", "Cashew processing unit", "జీడిమామిడి ప్రాసెసింగ్ యూనిట్"),
    ("coffee_yard", "Coffee pulping or drying yard (GCC or FPO)", "కాఫీ పల్పింగ్ లేదా ఎండబెట్టే యార్డ్ (GCC లేదా FPO)"),
    ("gcc_depot_santha", "GCC depot or weekly santha", "GCC డిపో లేదా వారపు సంత"),
    ("market_yard_rsk", "Market yard or RSK (government buying centre)", "మార్కెట్ యార్డ్ లేదా RSK (ప్రభుత్వ కొనుగోలు కేంద్రం)"),
    ("handloom_shed", "Handloom common work shed or dyeing unit", "చేనేత ఉమ్మడి పని షెడ్ లేదా డైయింగ్ యూనిట్"),
    ("canal_irrigation", "Canal, tank or lift irrigation", "కాలువ, చెరువు లేదా లిఫ్ట్ ఇరిగేషన్"),
    ("iti_skill_centre", "ITI, skill centre or training centre", "ITI, నైపుణ్య కేంద్రం లేదా శిక్షణ కేంద్రం"),
    ("other", "Other (specify)", "ఇతర (తెలపండి)"),
    ("none", "None, I could use all that are in my area", "ఏదీ లేదు, నా ప్రాంతంలో ఉన్నవన్నీ వాడుకోగలిగాను"),
    ("no_facility", "There is no such facility in my area", "నా ప్రాంతంలో అలాంటి సదుపాయం లేదు"),
]
for name, en, te in facilities_list:
    choice("facilities_unused", name, en, te)

# =====================================================================
# SETTINGS
# =====================================================================
ws3 = wb.create_sheet("settings")
ws3.append(["form_title", "form_id", "version", "default_language", "allow_choice_duplicates"])
ws3.append(["North Andhra Livelihoods Survey",
            "na_livelihoods_survey", "20261013", "English (en)", "yes"])

wb.save("North Andhra Livelihoods Survey_FINAL.xlsx")
print("Saved FINAL XLSForm (KoboToolbox + ODK Central/Collect compatible).")
