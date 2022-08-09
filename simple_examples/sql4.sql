SELECT MIN(ci.name) AS uncredited_voiced_character
FROM cast_info AS ci,
     company_name AS cn
WHERE ci.note LIKE '%(voice)%'
  AND ci.note LIKE '%(uncredited)%'
  AND cn.country_code = '[fi]';