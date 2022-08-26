SELECT MIN(t.title) AS german_movie
FROM kind_type AS kt,
     movie_companies AS mc,
     title AS t
WHERE kt.kind ='movie'
  AND kt.id = t.kind_id
  AND mc.movie_id = t.id;