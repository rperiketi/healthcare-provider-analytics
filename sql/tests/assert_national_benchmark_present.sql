-- Every state service row needs a national rate to compare against
SELECT year, state, hcpcs_cd, place_of_service
FROM fct_service_reimbursement
WHERE state <> 'US' AND national_avg_payment_per_service IS NULL AND services > 0;
