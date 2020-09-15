--Return all unique combinations of first and last names.
SELECT DISTINCT namefirst,namelast
FROM people;

--Count the number of records of players at least 72 inches tall who were not born in the USA.
SELECT *
FROM people
WHERE height>=72
AND birthcountry!='USA';

--Return the average weight for players grouped by birth year, in descending order of birth year. (For mathematical results, it is usually nicer to ROUND your results to avoid floats with many significant digits)
SELECT ROUND(AVG(weight),0) AS avg_weight, birthyear
FROM people
GROUP BY birthyear
ORDER BY birthyear DESC;

--Return the maximum salary paid for each year. Sort the results from high to low.
SELECT yearid, MAX(salary) AS max_salary
FROM salaries
GROUP BY yearid
ORDER BY max_salary DESC;

--Return the average salary paid by each team for each season. Sort the results by year, league and team.
SELECT yearid, lgid, teamid, ROUND(AVG(salary),0) AS avg_salary
FROM salaries
GROUP BY yearid,lgid,teamid
ORDER BY yearid,lgid,teamid;

