SELECT MIN(n.name) AS of_person
FROM aka_name AS an,
     name AS n,
     person_info AS pi
WHERE n.gender='m'
  AND pi.note ='Volker Boehm'
  AND n.id = an.person_id
  AND n.id = pi.person_id
  AND pi.person_id = an.person_id;