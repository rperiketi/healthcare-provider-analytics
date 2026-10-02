-- Every state-year in the supply fact must have a population
SELECT state, year FROM fct_state_supply WHERE population IS NULL OR population <= 0;
