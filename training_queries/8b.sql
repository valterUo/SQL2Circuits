SELECT MIN(an1.name) AS actress_pseudonym
FROM aka_name AS an1,
     cast_info AS ci,
     name AS n1
WHERE ci.note ='(voice: English version)'
  AND n1.name LIKE '%Yo%'
  AND an1.person_id = n1.id
  AND n1.id = ci.person_id
  AND an1.person_id = ci.person_id;