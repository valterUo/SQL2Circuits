SELECT MIN(lt.link) AS movie_link_type,
       MIN(t.title) AS non_polish_sequel_movie
FROM link_type AS lt,
     movie_link AS ml,
     title AS t
WHERE lt.id = ml.link_type_id
  AND ml.movie_id = t.id
  AND lt.link LIKE '%follow%';