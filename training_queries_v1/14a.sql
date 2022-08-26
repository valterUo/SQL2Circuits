SELECT MIN(t.title) AS northern_dark_movie
FROM movie_info AS mi,
     title AS t
WHERE mi.info IN ('Sweden',
                  'German',
                  'USA')
  AND t.production_year > 2010
  AND t.id = mi.movie_id;