SELECT MIN(t.production_year) AS movie_year
FROM company_type AS ct,
     movie_companies AS mc,
     title AS t
WHERE ct.id = mc.company_type_id
  AND t.id = mc.movie_id;