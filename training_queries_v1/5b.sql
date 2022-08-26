SELECT MIN(t.title) AS typical_european_movie
FROM info_type AS it,
     movie_companies AS mc,
     movie_info AS mi,
     title AS t
WHERE t.id = mi.movie_id
  AND t.id = mc.movie_id
  AND mc.movie_id = mi.movie_id
  AND it.id = mi.info_type_id;