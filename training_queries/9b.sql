SELECT MIN(chn.name) AS character_name
FROM char_name AS chn,
     cast_info AS ci
WHERE ci.note IN ('(voice)',
                  '(voice: Japanese version)',
                  '(voice) (uncredited)',
                  '(voice: English version)')
  AND chn.id = ci.person_role_id;