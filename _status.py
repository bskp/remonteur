#!/usr/bin/env python

from schema import db, Line, Movie

print     'Movie            Lines   Snippets    Pitches'

for movie in Movie.select():
    print '%15s %i      %i          %i' % (movie.title,
                                                       movie.lines_complete,
                                                       movie.snippets_complete,
                                                       movie.pitches_complete,
                                                       )
