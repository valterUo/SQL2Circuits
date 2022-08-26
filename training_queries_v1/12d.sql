SELECT MIN(t.title) AS drama_horror_movie
FROM movie_companies AS mc,
     movie_info AS mi,
     title AS t
WHERE mi.info IN ('Drama',
                  'Horror')
  AND t.id = mc.movie_id
  AND mc.movie_id = mi.movie_id;