SELECT MIN(cn.name) AS producing_company,
       MIN(t.title) AS movie_about_winning
FROM company_name AS cn,
     movie_companies AS mc,
     title AS t
WHERE t.title != ''
  AND mc.movie_id = t.id
  AND cn.id = mc.company_id;