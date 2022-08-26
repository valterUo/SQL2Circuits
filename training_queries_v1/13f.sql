SELECT MIN(t.title) AS movie_about_winning
FROM kind_type AS kt,
     title AS t
WHERE kt.kind = 'movie'
  AND t.title != ''
  AND kt.id = t.kind_id;