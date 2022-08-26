SELECT MIN(n.name) AS of_person
FROM cast_info AS ci,
     link_type AS lt,
     name AS n,
     person_info AS pi
WHERE lt.link ='features'
  AND n.name_pcode_cf LIKE 'D%'
  AND n.id = pi.person_id
  AND ci.person_id = n.id;