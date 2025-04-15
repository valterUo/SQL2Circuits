SELECT MIN(t.title) AS movie_title
FROM info_type AS it,
     keyword AS k,
     movie_keyword AS mk,
     title AS t
WHERE it.info ='rating'
  AND k.keyword LIKE '%sequel%'
  AND t.production_year > 2010
  AND t.id = mk.movie_id
  AND k.id = mk.keyword_id;