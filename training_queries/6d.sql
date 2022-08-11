SELECT MIN(k.keyword) AS movie_keyword
FROM keyword AS k,
     movie_keyword AS mk
WHERE k.id = mk.keyword_id;