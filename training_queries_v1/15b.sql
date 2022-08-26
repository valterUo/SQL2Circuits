SELECT MIN(mi.info) AS release_date
FROM aka_title AS at,
     info_type AS it1,
     movie_info AS mi
WHERE mi.note LIKE '%internet%'
  AND mi.movie_id = at.movie_id
  AND it1.id = mi.info_type_id;