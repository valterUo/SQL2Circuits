SELECT MIN(cn.name) AS from_company
FROM company_name AS cn,
     company_type AS ct,
     movie_companies AS mc
WHERE mc.company_type_id = ct.id
  AND mc.company_id = cn.id;