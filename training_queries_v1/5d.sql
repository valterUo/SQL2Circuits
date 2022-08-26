SELECT MIN(mc.note) AS note
FROM info_type AS it,
     movie_companies AS mc,
     movie_info AS mi
WHERE mc.movie_id = mi.movie_id
  AND it.id = mi.info_type_id;