SELECT MIN(n.name) AS of_person,
       MIN(t.title) AS biography_movie
FROM aka_name AS an,
     cast_info AS ci,
     name AS n,
     title AS t
WHERE n.id = an.person_id
  AND ci.person_id = n.id
  AND t.id = ci.movie_id;