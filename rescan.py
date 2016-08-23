#!/usr/bin/env python

import os
import subprocess
import pysrt as srt
import progressbar

from db import db, Line, Movie

FFMPEG_BIN = 'ffmpeg'

MOVIES_DIR = 'movies/'
SUBTITLE_EXT = '.srt'
MOVIE_EXT = '.mkv', '.mp4', '.avi'

IGNORE_LINES = '['

SNIPPET_MARGIN_BEFORE = 0.2 # seconds
SNIPPET_MARGIN_AFTER = 0.1 # seconds

def rescan_dir():
    db_movies = [m.title for m in Movie.select(Movie.title)]

    print "Rescanning movie directory..."

    # Add all new movies to DB
    for item in os.listdir(MOVIES_DIR):
        path = os.path.join(MOVIES_DIR, item)
        if os.path.isfile(path):
            continue

        if item in db_movies:
            db_movies.remove(item)
            continue

        # Create new movie
       
        files = os.listdir(path)
        subtitles = [f for f in files if f.endswith(SUBTITLE_EXT)]
        video = [f for f in files if f.endswith(MOVIE_EXT)]

        if not subtitles:
            print "No subtitle file found for '%s'. Please add and rescan!" % item
            continue
        else:
            subtitles = os.path.join(path, subtitles[0])

        if not video:
            print "No movie file found for '%s'. Please add and rescan!" % item
            continue
        else:
            video = os.path.join(path, video[0])

        m = Movie.create(title=item,
                         subtitles=subtitles,
                         video=video
                         )
        m.save()

    # Remove gone movies from DB
    for movie in db_movies:
        m = Movie.get(Movie.title==movie)
        m.delete_instance()
        # TODO remove snippets and lines as well!


    print 'done.'


def create_lines():
    for movie in Movie.select().where(Movie.lines_complete == False):

        print "Reading subtitles for '%s'" % movie.title
        lines = srt.open(movie.subtitles)

        for line in movie.lines:
            line.delete_instance()

        bar = progressbar.ProgressBar()
        for line in bar(lines):

            # Skip subtitles matching a certain pattern
            if line.text.startswith( IGNORE_LINES ):
                continue

            to_seconds = lambda t: t.milliseconds/1000.0 \
                                 + t.seconds \
                                 + t.minutes * 60.0 \
                                 + t.hours * 3600.0

            # Skip all subtitles at the beginning of the movie
            if to_seconds(line.start) < 5:
                continue

            start = to_seconds(line.start)
            duration = to_seconds(line.duration)

            l = Line.create(text=line.text,
                            movie=movie,
                            start=start,
                            duration=duration
                            )

            l.save()

        movie.lines_complete = True
        movie.save()


def create_snippets():
    for movie in Movie.select().where(Movie.snippets_complete == False):

        print "Creating audio snippets for '%s'" % movie.title

        # create snippet folder
        path = os.path.join(MOVIES_DIR, movie.title, 'snippets')
        try: 
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise

        # create audio snippets for each line

        bar = progressbar.ProgressBar()
        for line in bar(movie.lines):
    
            command = [FFMPEG_BIN,
                       '-i', movie.video,
                       '-ss', '%.2f' % (line.start - SNIPPET_MARGIN_BEFORE),
                       '-t', '%.2f' % (line.duration + SNIPPET_MARGIN_BEFORE \
                                       + SNIPPET_MARGIN_AFTER),
                       '-vn', 
                       '-loglevel', 'panic',
                       '-acodec', 'copy', os.path.join(path, '%i.aac' % line.id)
                       ]

            subprocess.check_output( command )
        
    movie.lines_complete = True
    movie.save()


rescan_dir()
create_lines()
create_snippets()





