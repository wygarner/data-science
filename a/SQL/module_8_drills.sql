-- Write a query that returns the namefirst and namelast fields of the people table, 
-- along with the inducted field from the hof_inducted table. All rows from the 
-- people table should be returned, and NULL values for the fields from hof_inducted 
-- should be returned when there is no match found.
SELECT namefirst, namelast, inducted
FROM people LEFT OUTER JOIN hof_inducted
ON people.playerid= hof_inducted.playerid;

-- In 2006, a special Baseball Hall of Fame induction was conducted for players 
-- from the negro baseball leagues of the 20th century. In that induction, 
-- 17 players were posthumously inducted into the Baseball Hall of Fame. 
-- Write a query that returns the first and last names, birth and death dates, 
-- and birth countries for these players. Note that the year of induction was 2006, 
-- and the value for votedby will be “Negro League.”
SELECT namefirst, namelast, birthyear, deathyear, birthcountry
FROM people LEFT OUTER JOIN hof_inducted
ON people.playerid= hof_inducted.playerid
WHERE yearid='2006' AND votedby= 'Negro League';

-- Write a query that returns the yearid, playerid, teamid, and salary fields 
-- from the salaries table, along with the category field from the hof_inducted table. 
-- Keep only the records that are in both salaries and hof_inducted. 
-- Hint: While a field named yearid is found in both tables, don’t JOIN by it. 
-- You must, however, explicitly name which field to include.
SELECT salaries.yearid, salaries.playerid, salaries.teamid, salary, category
FROM salaries LEFT OUTER JOIN hof_inducted
ON salaries.playerid= hof_inducted.playerid
WHERE category IS NOT NULL;

-- Write a query that returns the playerid, yearid, teamid, lgid, and salary fields 
-- from the salaries table and the inducted field from the hof_inducted table. 
-- Keep all records from both tables.
SELECT salaries.playerid, salaries.yearid, salaries.teamid, salaries.lgid, salary, inducted
FROM salaries LEFT OUTER JOIN hof_inducted
ON salaries.playerid= hof_inducted.playerid;

-- There are 2 tables, hof_inducted and hof_not_inducted, indicating successful 
-- and unsuccessful inductions into the Baseball Hall of Fame, respectively.
-- Combine these 2 tables by all fields. Keep all records.
-- Get a distinct list of all player IDs for players who have been put up 
-- for HOF induction.
SELECT * FROM hof_inducted
UNION ALL
SELECT * FROM hof_not_inducted;

SELECT playerid FROM hof_inducted
UNION
SELECT playerid FROM hof_not_inducted;

-- Write a query that returns the last name, first name (see people table), 
-- and total recorded salaries for all players found in the salaries table.
SELECT namefirst, namelast, SUM(salary) AS total_salary
FROM people JOIN salaries
ON people.playerid= salaries.playerid
GROUP BY namelast, namefirst;

-- Write a query that returns all records from the hof_inducted and hof_not_inducted tables that 
-- include playerid, yearid, namefirst, and namelast. Hint: Each FROM statement will include a LEFT OUTER JOIN!
SELECT hof_inducted.playerid, yearid, namefirst, namelast 
FROM hof_inducted LEFT OUTER JOIN people
ON hof_inducted.playerid = people.playerid

UNION ALL 

SELECT hof_not_inducted.playerid, yearid, namefirst, namelast 
FROM hof_not_inducted LEFT OUTER JOIN people
ON hof_not_inducted.playerid = people.playerid;

-- Return a table including all records from both hof_inducted and hof_not_inducted, and include a new field, 
-- namefull, which is formatted as namelast , namefirst (in other words, the last name, followed by a comma, 
-- then a space, then the first name). The query should also return the yearid and inducted fields. 
-- Include only records since 1980 from both tables. Sort the resulting table by yearid, then inducted so 
-- that Y comes before N. Finally, sort by the namefull field, A to Z.
SELECT concat(namelast,', ', namefirst) AS namefull, yearid, inducted
FROM hof_inducted LEFT OUTER JOIN people
ON hof_inducted.playerid = people.playerid
WHERE yearid >= 1980

UNION ALL 

SELECT concat(namelast,', ', namefirst) AS namefull, yearid, inducted
FROM hof_not_inducted LEFT OUTER JOIN people
ON hof_not_inducted.playerid = people.playerid
WHERE yearid >= 1980

ORDER BY yearid,  inducted DESC, namefull;

-- Write a query that returns the highest annual salary for each teamid, ranked from high to low, 
-- along with the corresponding playerid.
WITH max AS
(SELECT MAX(salary) as max_salary, teamid, yearid
FROM salaries
GROUP BY teamid, yearid)
SELECT salaries.yearid, salaries.teamid, playerid, max.max_salary
FROM max LEFT OUTER JOIN salaries
ON salaries.teamid = max.teamid AND salaries.yearid = max.yearid AND salaries.salary = max.max_salary
ORDER BY max.max_salary DESC;

-- Select birthyear, deathyear, namefirst, and namelast of all the players born since the birth year 
-- of Babe Ruth (playerid = ruthba01). Sort the results by birth year from low to high.
SELECT birthyear, deathyear, namefirst, namelast
FROM people
WHERE birthyear > ANY
	(SELECT	birthyear
	FROM people
	WHERE playerid = 'ruthba01')
ORDER BY birthyear;

-- Using the people table, write a query that returns namefirst, namelast, and a field called usaborn. 
-- The usaborn field should show the following: if the player's birthcountry is the USA, then the record is 'USA.'
-- Otherwise, it's 'non-USA.' Order the results by 'non-USA' records first.
SELECT namefirst, namelast, 
	CASE
		WHEN birthcountry = 'USA' THEN 'USA'
		ELSE 'non-USA'
	END AS usaborn
FROM people
ORDER BY 3;

-- Calculate the average height for players throwing with their right hand versus their left hand. 
-- Name these fields right_height and left_height, respectively.
SELECT
AVG(CASE WHEN throws = 'R' THEN height END) AS right_height,
AVG(CASE WHEN throws = 'L' THEN height END) AS left_height
FROM people;







