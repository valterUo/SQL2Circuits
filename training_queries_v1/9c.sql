SELECT MIN(t.title) AS movie
FROM movie_companies AS mc,
     title AS t
WHERE mc.note LIKE '%(USA)%'
  AND t.production_year >= 2005 
  AND t.production_year <= 2015
  AND t.id = mc.movie_id;