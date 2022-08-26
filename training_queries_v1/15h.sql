SELECT MIN(t.title) AS internet_movie
FROM movie_companies AS mc,
     title AS t
WHERE mc.note LIKE '%(200%)%'
  AND t.production_year > 2000
  AND t.id = mc.movie_id;