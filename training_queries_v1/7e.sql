SELECT MIN(t.title) AS biography_movie
FROM cast_info AS ci,
     person_info AS pi,
     title AS t
WHERE t.production_year >= 1980 
  AND t.production_year <= 1984
  AND t.id = ci.movie_id
  AND pi.person_id = ci.person_id;