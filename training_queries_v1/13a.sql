SELECT MIN(mi.info) AS release_date
FROM company_name AS cn,
     movie_companies AS mc,
     movie_info AS mi
WHERE cn.country_code ='[de]'
  AND cn.id = mc.company_id
  AND mi.movie_id = mc.movie_id;