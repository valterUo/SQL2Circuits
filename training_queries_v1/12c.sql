SELECT MIN(t.title) AS drama_horror_movie
FROM movie_info AS mi,
     title AS t
WHERE t.production_year >= 2005 
  AND t.production_year <= 2008
  AND t.id = mi.movie_id;