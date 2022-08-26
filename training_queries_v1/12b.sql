SELECT MIN(cn.name) AS movie_company
FROM company_name AS cn,
     company_type AS ct,
     movie_companies AS mc
WHERE cn.country_code = '[us]'
  AND ct.kind = 'production companies'
  AND ct.id = mc.company_type_id
  AND cn.id = mc.company_id;