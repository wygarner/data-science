-- Return the category name and average length per category for all films, 
-- excluding those rated G. Return only those categories with an average length 
-- of more than 120 minutes. Sort the results alphabetically.
SELECT category.name, ROUND(AVG(film.length),0) as avg_length
FROM film LEFT OUTER JOIN film_category
ON film.film_id= film_category.film_id
LEFT OUTER JOIN category
ON category.category_id= film_category.category_id
WHERE rating!='G'
GROUP BY film_category.category_id, category.name
HAVING AVG(film.length)>=120
ORDER BY category.name;

-- Return the country name and average rental time for all rentals, 
-- grouped by customer’s country and only for average rental times under 5 days. 
-- (Pay close attention to the format of the time interval).
SELECT country.country, AVG(return_date-rental_date)
FROM country LEFT OUTER JOIN city
ON country.country_id= city.country_id
LEFT OUTER JOIN address
ON city.city_id= address.city_id
LEFT OUTER JOIN customer
ON address.address_id= customer.address_id
LEFT OUTER JOIN rental
ON customer.customer_id= rental.customer_id
GROUP BY country.country
HAVING AVG(return_date-rental_date)< '5 days';

-- Return a list of last names of both customers and actors whose 
-- last names start with D, sorted alphabetically.
SELECT last_name FROM customer
WHERE LEFT(last_name,1)='D'
UNION
SELECT last_name FROM actor
WHERE LEFT(last_name,1)='D'