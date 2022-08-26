SELECT MIN(cn.name) AS movie_company
FROM company_name AS cn,
     movie_companies AS mc,
     movie_info AS mi
WHERE cn.country_code = '[us]'
  AND mi.info IN ('Drama',
                  'Horror')
  AND cn.id = mc.company_id
  AND mc.movie_id = mi.movie_id;