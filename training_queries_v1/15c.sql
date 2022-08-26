SELECT MIN(mi.info) AS release_date
FROM info_type AS it1,
     movie_companies AS mc,
     movie_info AS mi
WHERE mi.note LIKE '%internet%'
  AND mi.movie_id = mc.movie_id
  AND it1.id = mi.info_type_id;