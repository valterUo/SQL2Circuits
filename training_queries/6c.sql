SELECT MIN(k.keyword) AS movie_keyword
FROM keyword AS k,
     movie_keyword AS mk,
     title AS t
WHERE k.id = mk.keyword_id
  AND t.id = mk.movie_id;