SELECT MIN(t.title) AS movie_title
FROM movie_companies AS mc,
     title AS t
WHERE mc.movie_id = t.id;