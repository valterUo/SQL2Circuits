SELECT MIN(t.title) AS north_european_dark_production
FROM info_type AS it1,
     movie_info AS mi,
     title AS t
WHERE it1.info = 'countries'
  AND t.id = mi.movie_id
  AND it1.id = mi.info_type_id;