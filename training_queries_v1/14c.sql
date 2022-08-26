SELECT MIN(t.title) AS north_european_dark_production
FROM keyword AS k,
     movie_keyword AS mk,
     title AS t
WHERE k.keyword IS NOT NULL
  AND k.keyword IN ('murder')
  AND t.id = mk.movie_id
  AND k.id = mk.keyword_id;