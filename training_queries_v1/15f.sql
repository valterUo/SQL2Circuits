SELECT MIN(mi.info) AS release_date
FROM aka_title AS at,
     movie_companies AS mc,
     movie_info AS mi
WHERE mi.info LIKE 'USA:% 200%'
  AND mi.movie_id = mc.movie_id
  AND mi.movie_id = at.movie_id;