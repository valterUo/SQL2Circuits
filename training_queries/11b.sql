SELECT MIN(t.title) AS non_polish_sequel_movie
FROM movie_companies AS mc,
     movie_keyword AS mk,
     title AS t
WHERE t.production_year >= 1950 
  AND t.production_year <= 2000
  AND t.id = mk.movie_id
  AND t.id = mc.movie_id
  AND mk.movie_id = mc.movie_id;