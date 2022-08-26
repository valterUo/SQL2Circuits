SELECT MIN(mi.info) AS release_date
FROM company_type AS ct,
     movie_companies AS mc,
     movie_info AS mi
WHERE ct.kind ='production companies'
  AND ct.id = mc.company_type_id
  AND mi.movie_id = mc.movie_id;