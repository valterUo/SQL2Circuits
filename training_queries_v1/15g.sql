SELECT MIN(t.title) AS internet_movie
FROM movie_info AS mi,
     title AS t
WHERE mi.note LIKE '%internet%'
  AND mi.info LIKE 'USA:% 200%'
  AND t.id = mi.movie_id;