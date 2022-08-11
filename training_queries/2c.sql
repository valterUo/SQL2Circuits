SELECT MIN(t.title) AS movie_title
FROM movie_companies AS mc,
     movie_keyword AS mk,
     title AS t
WHERE mc.movie_id = t.id
  AND t.id = mk.movie_id
  AND mc.movie_id = mk.movie_id;