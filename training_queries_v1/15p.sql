SELECT MIN(mi.info) AS release_date,
       MIN(t.title) AS internet_movie
FROM movie_info AS mi,
     title AS t
WHERE t.production_year > 2000
  AND t.id = mi.movie_id;