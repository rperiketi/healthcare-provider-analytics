SELECT state, access_gap_score FROM mart_state_gap
WHERE access_gap_score IS NULL OR access_gap_score NOT BETWEEN 0 AND 100;
