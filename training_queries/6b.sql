SELECT MIN(k.keyword) AS movie_keyword
FROM keyword AS k,
     title AS t
WHERE k.keyword = 'marvel-cinematic-universe'
  AND t.production_year > 2010;