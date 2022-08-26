SELECT MIN(mi.info) AS release_date
FROM movie_companies AS mc,
     movie_info AS mi
WHERE mc.note LIKE '%(200%)%'
  AND mc.note LIKE '%(worldwide)%'
  AND mi.note LIKE '%internet%'
  AND mi.info LIKE 'USA:% 200%'
  AND mi.movie_id = mc.movie_id;