SELECT MIN(cn.name) AS producing_company
FROM company_name AS cn,
     company_type AS ct,
     movie_companies AS mc
WHERE cn.country_code ='[de]'
  AND ct.kind ='production companies'
  AND cn.id = mc.company_id
  AND ct.id = mc.company_type_id;