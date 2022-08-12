SELECT MIN(an.name) AS alternative_name,
       MIN(chn.name) AS character_name
FROM aka_name AS an,
     char_name AS chn,
     cast_info AS ci
WHERE chn.id = ci.person_role_id
  AND an.person_id = ci.person_id;