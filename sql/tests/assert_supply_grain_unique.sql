SELECT state, year, bh_category, count(*) AS n
FROM fct_state_supply GROUP BY ALL HAVING count(*) > 1;
