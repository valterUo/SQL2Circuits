SELECT MIN(mi.info) AS release_date
FROM info_type AS it1,
     movie_info AS mi,
     movie_keyword AS mk
WHERE mi.note LIKE '%internet%'
  AND mk.movie_id = mi.movie_id
  AND it1.id = mi.info_type_id;