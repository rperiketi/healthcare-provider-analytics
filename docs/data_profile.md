# Data Profile Report

## 1. File inventory

| File | Rows | Columns | Encoding |
|---|---:|---:|---|
| cdc_mental_health_care.csv | 10,404 | 15 | utf-8 |
| geo_service_2019.csv | 273,211 | 15 | utf-8 |
| geo_service_2020.csv | 268,149 | 15 | utf-8 |
| geo_service_2021.csv | 271,635 | 15 | utf-8 |
| geo_service_2022.csv | 270,673 | 15 | utf-8 |
| geo_service_2023.csv | 268,634 | 15 | utf-8 |
| geo_service_2024.csv | 268,350 | 15 | utf-8 |
| provider_2019.csv | 1,155,870 | 81 | utf-8 |
| provider_2020.csv | 1,161,542 | 81 | utf-8 |
| provider_2021.csv | 1,198,754 | 81 | utf-8 |
| provider_2022.csv | 1,230,293 | 81 | utf-8 |
| provider_2023.csv | 1,259,343 | 81 | utf-8 |
| provider_2024.csv | 1,296,739 | 81 | utf-8 |

## 2. Schema drift across years

**provider**: 81 distinct columns across [2019, 2020, 2021, 2022, 2023, 2024]
- No drift: identical columns every year

Columns (provider 2024): `Rndrng_NPI`, `Rndrng_Prvdr_Last_Org_Name`, `Rndrng_Prvdr_First_Name`, `Rndrng_Prvdr_MI`, `Rndrng_Prvdr_Crdntls`, `Rndrng_Prvdr_Ent_Cd`, `Rndrng_Prvdr_St1`, `Rndrng_Prvdr_St2`, `Rndrng_Prvdr_City`, `Rndrng_Prvdr_State_Abrvtn`, `Rndrng_Prvdr_State_FIPS`, `Rndrng_Prvdr_Zip5`, `Rndrng_Prvdr_RUCA`, `Rndrng_Prvdr_RUCA_Desc`, `Rndrng_Prvdr_Cntry`, `Rndrng_Prvdr_Type`, `Rndrng_Prvdr_Mdcr_Prtcptg_Ind`, `Tot_HCPCS_Cds`, `Tot_Benes`, `Tot_Srvcs`, `Tot_Sbmtd_Chrg`, `Tot_Mdcr_Alowd_Amt`, `Tot_Mdcr_Pymt_Amt`, `Tot_Mdcr_Stdzd_Amt`, `Drug_Sprsn_Ind`, `Drug_Tot_HCPCS_Cds`, `Drug_Tot_Benes`, `Drug_Tot_Srvcs`, `Drug_Sbmtd_Chrg`, `Drug_Mdcr_Alowd_Amt`, `Drug_Mdcr_Pymt_Amt`, `Drug_Mdcr_Stdzd_Amt`, `Med_Sprsn_Ind`, `Med_Tot_HCPCS_Cds`, `Med_Tot_Benes`, `Med_Tot_Srvcs`, `Med_Sbmtd_Chrg`, `Med_Mdcr_Alowd_Amt`, `Med_Mdcr_Pymt_Amt`, `Med_Mdcr_Stdzd_Amt`, `Bene_Avg_Age`, `Bene_Age_LT_65_Cnt`, `Bene_Age_65_74_Cnt`, `Bene_Age_75_84_Cnt`, `Bene_Age_GT_84_Cnt`, `Bene_Feml_Cnt`, `Bene_Male_Cnt`, `Bene_Race_Wht_Cnt`, `Bene_Race_Black_Cnt`, `Bene_Race_API_Cnt`, `Bene_Race_Hspnc_Cnt`, `Bene_Race_NatInd_Cnt`, `Bene_Race_Othr_Cnt`, `Bene_Dual_Cnt`, `Bene_Ndual_Cnt`, `Bene_CC_BH_ADHD_OthCD_V1_Pct`, `Bene_CC_BH_Alcohol_Drug_V1_Pct`, `Bene_CC_BH_Tobacco_V1_Pct`, `Bene_CC_BH_Alz_NonAlzdem_V2_Pct`, `Bene_CC_BH_Anxiety_V1_Pct`, `Bene_CC_BH_Bipolar_V1_Pct`, `Bene_CC_BH_Mood_V2_Pct`, `Bene_CC_BH_Depress_V1_Pct`, `Bene_CC_BH_PD_V1_Pct`, `Bene_CC_BH_PTSD_V1_Pct`, `Bene_CC_BH_Schizo_OthPsy_V1_Pct`, `Bene_CC_PH_Asthma_V2_Pct`, `Bene_CC_PH_Afib_V2_Pct`, `Bene_CC_PH_Cancer6_V2_Pct`, `Bene_CC_PH_CKD_V2_Pct`, `Bene_CC_PH_COPD_V2_Pct`, `Bene_CC_PH_Diabetes_V2_Pct`, `Bene_CC_PH_HF_NonIHD_V2_Pct`, `Bene_CC_PH_Hyperlipidemia_V2_Pct`, `Bene_CC_PH_Hypertension_V2_Pct`, `Bene_CC_PH_IschemicHeart_V2_Pct`, `Bene_CC_PH_Osteoporosis_V2_Pct`, `Bene_CC_PH_Parkinson_V2_Pct`, `Bene_CC_PH_Arthritis_V2_Pct`, `Bene_CC_PH_Stroke_TIA_V2_Pct`, `Bene_Avg_Risk_Scre`

**geo_service**: 15 distinct columns across [2019, 2020, 2021, 2022, 2023, 2024]
- No drift: identical columns every year

Columns (geo_service 2024): `Rndrng_Prvdr_Geo_Lvl`, `Rndrng_Prvdr_Geo_Cd`, `Rndrng_Prvdr_Geo_Desc`, `HCPCS_Cd`, `HCPCS_Desc`, `HCPCS_Drug_Ind`, `Place_Of_Srvc`, `Tot_Rndrng_Prvdrs`, `Tot_Benes`, `Tot_Srvcs`, `Tot_Bene_Day_Srvcs`, `Avg_Sbmtd_Chrg`, `Avg_Mdcr_Alowd_Amt`, `Avg_Mdcr_Pymt_Amt`, `Avg_Mdcr_Stdzd_Amt`


## 3. Provider file checks (provider_2024.csv)

- Key `Rndrng_NPI`: 1,296,739 rows, 1,296,739 distinct, 0 duplicates
- Columns with blanks: 61 of 81

| Column | % blank |
|---|---:|
| Med_Sprsn_Ind | 88.3 |
| Drug_Sprsn_Ind | 88.3 |
| Bene_Race_API_Cnt | 81.9 |
| Rndrng_Prvdr_St2 | 81.2 |
| Bene_Race_Othr_Cnt | 81.2 |
| Bene_Race_Hspnc_Cnt | 76.3 |
| Bene_Race_Black_Cnt | 71.3 |
| Bene_CC_BH_PTSD_V1_Pct | 68.0 |
| Bene_CC_BH_ADHD_OthCD_V1_Pct | 67.5 |
| Bene_CC_BH_PD_V1_Pct | 65.7 |
| Bene_Race_NatInd_Cnt | 65.5 |
| Bene_CC_PH_Parkinson_V2_Pct | 62.0 |
| Bene_CC_BH_Schizo_OthPsy_V1_Pct | 59.2 |
| Bene_CC_BH_Bipolar_V1_Pct | 56.7 |
| Bene_Age_LT_65_Cnt | 53.3 |
| Bene_Age_GT_84_Cnt | 52.3 |
| Bene_CC_BH_Alcohol_Drug_V1_Pct | 48.4 |
| Bene_CC_BH_Alz_NonAlzdem_V2_Pct | 43.1 |
| Bene_CC_PH_Stroke_TIA_V2_Pct | 40.8 |
| Bene_CC_BH_Tobacco_V1_Pct | 40.3 |
| Rndrng_Prvdr_MI | 37.5 |
| Bene_CC_PH_Asthma_V2_Pct | 37.1 |
| Bene_Ndual_Cnt | 35.8 |
| Bene_Dual_Cnt | 35.8 |
| Bene_Race_Wht_Cnt | 35.7 |

**Provider types:** 113 distinct in `Rndrng_Prvdr_Type`. Behavioral-health candidates by year:

| Provider type | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|
| Addiction Medicine | 230 | 226 | 246 | 250 | 257 | 280 |
| Geriatric Psychiatry | 195 | 185 | 185 | 177 | 169 | 164 |
| Licensed Clinical Social Worker | 21,775 | 19,329 | 18,216 | 17,459 | 17,207 | 16,435 |
| Licensed Professional Counselor | 0 | 0 | 0 | 0 | 0 | 3,030 |
| Marriage and Family Therapist | 0 | 0 | 0 | 0 | 0 | 428 |
| Neuropsychiatry | 124 | 126 | 135 | 146 | 156 | 202 |
| Psychiatry | 21,988 | 21,159 | 20,760 | 20,342 | 19,904 | 19,778 |
| Psychologist, Clinical | 16,203 | 14,513 | 13,572 | 12,949 | 12,540 | 11,986 |

## 4. Geography & service checks

| Year | Geo levels | Distinct HCPCS | Behavioral-health HCPCS rows |
|---|---|---:|---:|
| 2019 | National, State | 8,853 | 826 |
| 2020 | National, State | 9,003 | 809 |
| 2021 | National, State | 9,125 | 811 |
| 2022 | National, State | 9,231 | 800 |
| 2023 | National, State | 9,297 | 809 |
| 2024 | National, State | 9,403 | 802 |

## 5. CDC Household Pulse checks

Columns: `Indicator`, `Group`, `State`, `Subgroup`, `Phase`, `Time Period`, `Time Period Label`, `Time Period Start Date`, `Time Period End Date`, `Value`, `LowCI`, `HighCI`, `Confidence Interval`, `Quartile Range`, `Suppression Flag`

**Indicator values:**
- Needed Counseling or Therapy But Did Not Get It, Last 4 Weeks (2,601 rows)
- Received Counseling or Therapy, Last 4 Weeks (2,601 rows)
- Took Prescription Medication for Mental Health And/Or Received Counseling or Therapy, Last 4 Weeks (2,601 rows)
- Took Prescription Medication for Mental Health, Last 4 Weeks (2,601 rows)

**Group values:**
- By Age (1,064 rows)
- By Disability status (168 rows)
- By Education (608 rows)
- By Gender identity (156 rows)
- By Presence of Symptoms of Anxiety/Depression (304 rows)
- By Race/Hispanic ethnicity (760 rows)
- By Sex (304 rows)
- By Sexual orientation (156 rows)
- By State (6,732 rows)
- National Estimate (152 rows)

- Date range: 2020-08-19 00:00:00 to 2022-05-09 00:00:00
- Blank `Value`: 490 of 10,404 rows (suppressed estimates)