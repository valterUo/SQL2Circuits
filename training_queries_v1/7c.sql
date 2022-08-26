SELECT MIN(t.title) AS biography_movie
FROM cast_info AS ci,
     name AS n,
     title AS t
WHERE n.gender='m'
  AND t.production_year >= 1980 
  AND t.production_year <= 1984
  AND ci.person_id = n.id
  AND t.id = ci.movie_id;