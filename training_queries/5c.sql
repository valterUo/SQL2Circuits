SELECT MIN(t.title) AS typical_european_movie
FROM info_type AS it,
     movie_info AS mi,
     title AS t
WHERE t.id = mi.movie_id
  AND it.id = mi.info_type_id;