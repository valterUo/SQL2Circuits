SELECT MIN(t.title) AS russian_movie
FROM cast_info AS ci,
     movie_companies AS mc,
     title AS t
WHERE t.id = mc.movie_id
  AND t.id = ci.movie_id
  AND ci.movie_id = mc.movie_id;