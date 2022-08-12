SELECT MIN(chn.name) AS uncredited_voiced_character
FROM char_name AS chn,
     cast_info AS ci,
     movie_companies AS mc
WHERE ci.movie_id = mc.movie_id
  AND chn.id = ci.person_role_id;