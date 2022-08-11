SELECT MIN(t.title) AS movie_title
FROM keyword AS k,
     movie_keyword AS mk,
     title AS t
WHERE t.id = mk.movie_id
  AND k.id = mk.keyword_id;