--Return all records of people not born in the USA whose first name starts with the letter Y.

SELECT *
FROM people
WHERE birthcountry!='USA'
AND LEFT(namefirst,1)='Y';

--Return all records of people born between 1980 and 1985 either throw or bat with their right arm.

SELECT *
FROM people
WHERE (bats='R' OR throws='R')
AND birthyear BETWEEN 1980 AND 1985;

--Select all records of people whose birth year is unknown.

SELECT *
FROM people
WHERE birthyear ISNULL;

--Select all records of people born in France, Germany or Italy.

SELECT *
FROM people
WHERE birthcountry IN('France','Germany','Italy');




