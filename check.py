#!/usr/bin/env python2
# vim: set fileencoding=utf-8

from __future__ import division

import os
import peewee as pw
import sys
import subprocess
import progressbar


import schema
DB_NAME = 'lines.db'

movies_dir = sys.argv[1]

db, Movie, Line = schema.connect( os.path.join(movies_dir, DB_NAME) )

        
def _full_path(target):
    if target == None:
        target = ''
    return os.path.join(movies_dir, target)

print "{:20s}                         | Video Sub Lines  Wav   None  False".format(str(Movie.select().count()) + " Movies")
print "---------------------------------------------+-----------------------------------"


for movie in Movie.select():
    video_ok = '✓' if os.path.isfile( _full_path( movie.video )) else '-'
    srt_ok = '✓' if os.path.isfile( _full_path( movie.subtitles )) else '-'
    
    lines = movie.lines.count()
    lines_none = movie.lines.where( Line.sextimate == None ).count()
    lines_false = movie.lines.where( Line.sextimate == False ).count()

    lines_wav = 0
    for line in movie.lines:
        if os.path.isfile( _full_path( line.audio ) ):
            lines_wav += 1

    if lines > 0:
        print "{:45s}|   {:4s}   {:3s} {:6d} {:5.0%} {:5.0%} {:5.0%}".format(movie.title, video_ok, srt_ok, lines,
            lines_wav/lines, (lines-lines_none)/lines, (lines-lines_false)/lines)
    else:
        print "{:45s}| {:6s} {:5s} {:6d} -".format(movie.title, video_ok, srt_ok, lines)

        
