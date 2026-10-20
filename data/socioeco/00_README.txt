Northern Andhra PC data packet (Sarkar BigQuery)
Project: sarkar-381705.ap_state
PCs: Visakhapatnam, Vizianagaram, Srikakulam, Anakapalli, Araku

Files:
- 01_pc_summary.csv — PC-level households, population, BPL proxy
- 02_pc_ac_summary.csv — PC × AC roll-up
- 03_hierarchy_pc_ac_mandal_secretariat_cluster.csv — full geography tree
- 04_secretariat_master.csv — secretariat counts + location + income proxies + BPL proxy
- 05_secretariat_occupation.csv — occupation person counts by secretariat
- 06_secretariat_caste_pct.csv — simplified caste bucket percentages
- 07_secretariat_religion_pct.csv — religion percentages
- 08_reference_mandals_ulbs.csv — distinct mandals / ULB types

Notes:
- Village (rural) and ward/cluster (urban) use CLUSTER_ID / CLUSTER_NAME from ap_locaion.
- BPL: no direct BPL flag in Sarkar; pct_bpl_proxy_hh = share of HH with any member in
  poverty-targeted schemes (Aasara, pensions, EBC Nestham, YSR Cheyutha, Vasathi/Vidya Deevena).
- Income: GOVTEMP_SAL (govt employees), INCOMETAX flag, avg electricity (SPDCL+EPDCL+CPDCL).
- Secretariat lat/long from ap_sec_loc (where available).
