-- Fact totals must equal row counts in the cleaned provider data
SELECT f.year, f.n_fact, s.n_stg
FROM (SELECT year, sum(providers) AS n_fact FROM fct_state_supply GROUP BY year) f
JOIN (SELECT year, count(*) AS n_stg FROM stg_bh_providers GROUP BY year) s USING (year)
WHERE f.n_fact <> s.n_stg;
