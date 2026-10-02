-- Expect 50 states + DC
SELECT count(*) AS n FROM dim_state HAVING count(*) <> 51;
