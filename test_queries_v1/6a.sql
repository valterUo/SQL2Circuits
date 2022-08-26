SELECT MIN(k.keyword) AS movie_keyword
FROM keyword AS k,
     movie_keyword AS mk,
     title AS t
WHERE k.keyword = 'marvel-cinematic-universe'
  AND t.production_year > 2010
  AND k.id = mk.keyword_id
  AND t.id = mk.movie_id;