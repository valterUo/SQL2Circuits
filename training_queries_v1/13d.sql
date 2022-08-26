SELECT MIN(t.title) AS german_movie
FROM info_type AS it2,
     movie_info AS mi,
     title AS t
WHERE it2.info ='release dates'
  AND mi.movie_id = t.id
  AND it2.id = mi.info_type_id;