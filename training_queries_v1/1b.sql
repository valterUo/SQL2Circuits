SELECT MIN(mc.note) AS production_note,
       MIN(t.title) AS movie_title
FROM company_type AS ct,
     movie_companies AS mc,
     title AS t
WHERE ct.id = mc.company_type_id
  AND t.id = mc.movie_id;