SELECT MIN(mi.info) AS budget
FROM info_type AS it1,
     movie_info AS mi
WHERE it1.info ='budget'
  AND mi.info_type_id = it1.id;