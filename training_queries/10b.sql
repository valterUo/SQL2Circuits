SELECT MIN(chn.name) AS uncredited_voiced_character
FROM char_name AS chn,
     cast_info AS ci
WHERE ci.note LIKE '%(voice)%'
  AND ci.note LIKE '%(uncredited)%'
  AND chn.id = ci.person_role_id;