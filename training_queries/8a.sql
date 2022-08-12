SELECT MIN(t.title) AS japanese_movie_dubbed
FROM cast_info AS ci,
     movie_companies AS mc,
     title AS t
WHERE ci.note ='(voice: English version)'
  AND ci.movie_id = t.id
  AND t.id = mc.movie_id
  AND ci.movie_id = mc.movie_id;