SELECT year, sum(share_of_bh_payment_pct) AS total
FROM mart_service_mix GROUP BY year
HAVING abs(sum(share_of_bh_payment_pct) - 100) > 0.5;
