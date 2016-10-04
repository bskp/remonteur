#!/usr/bin/env python

import os
import sys
import subprocess
import progressbar

import caffeine  # prevent macOS from sleeping

import pysrt as srt
import numpy as np

from scipy import signal as sg
from scipy import stats as st

import amfm_decompy.pYAAPT as pYAAPT
import amfm_decompy.basic_tools as basic

from schema import Line, Movie, db


#
# Configuration
#

FFMPEG_BIN = 'ffmpeg'

DEFAULT_MOVIES_DIR = 'movies'

SUBTITLE_EXT = '.srt'
MOVIE_EXT = '.mkv', '.mp4', '.avi'

IGNORE_LINES = '['

SNIPPET_MARGIN_BEFORE = 0.2  # seconds
SNIPPET_MARGIN_AFTER = 0.1  # seconds
SNIPPET_EXT = '.wav'

#
# Helpers
#


def chunks(l, n):
    '''Yield successive n-sized chunks from l.'''
    for i in range(0, len(l), n):
        yield l[i:i + n]

#
# Steps
#

movies_dir = '/Volumes/LORA/filme'

def parse_args():
    global movies_dir
    args = sys.argv()

    if len(args) > 1:
        movies_dir = args[1]


def rescan_dir():
    ''' Sync the sqlite DB with the contents of the "movies" directory. '''

    db_movies = [m.title for m in Movie.select(Movie.title)]

    print "Rescanning movie directory..."

    # Add all new movies to DB
    for item in os.listdir(movies_dir):
        abs_path = os.path.join(movies_dir, item)
        path = item

        if os.path.isfile(abs_path):
            continue

        if item in db_movies:
            db_movies.remove(item)
            continue

        # Create new movie

        files = os.listdir(abs_path)
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
        print "Removing '%s'." % movie
        m = Movie.get(Movie.title == movie)
        m.delete_instance(recursive=True)


def create_lines():
    ''' Generate DB instances for every spoken line in every movie. '''

    for movie in Movie.select().where(Movie.skip_line == False):

        print "Reading subtitles for '%s'" % movie.title
        try:
            lines = srt.open(_full_path(movie.subtitles))
        except UnicodeDecodeError:
            print 'Non-UTF8-Subtitles. Falling back to iso-8859-1...'
            lines = srt.open(_full_path(movie.subtitles), encoding='iso-8859-1')

        for line in movie.lines:
            line.delete_instance()

        bar = progressbar.ProgressBar()
        for line in bar(lines):

            # Skip subtitles matching a certain pattern
            if line.text.startswith( IGNORE_LINES ):
                continue

            def to_seconds(t):
                return t.milliseconds / 1000.0 \
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

        movie.skip_line = True
        movie.save()


def create_snippets():
    ''' Generate audio snippets for every line. '''

    for movie in Movie.select().where(
            Movie.skip_line == True,
            Movie.skip_snippet == False):

        with db.transaction():

            print "Creating audio snippets for '%s'" % movie.title

            # create snippet folder
            path = os.path.join(movies_dir, movie.title, 'snippets')
            try:
                os.makedirs(path)
            except OSError:
                if os.path.isdir(path):
                    for f in os.listdir(path):
                        os.remove( os.path.join(path, f) )
                else:
                    raise

            # create audio snippets for each line
            bar = progressbar.ProgressBar()
            target = None
            target_ = None
            for group in bar(list(chunks(movie.lines, 32))):
                command = [FFMPEG_BIN,
                           '-i', _full_path(movie.video),
                           '-loglevel', 'panic',
                           ]

                for line in group:
                    target_ = target
                    target = os.path.join(path, '%i' % line.start + SNIPPET_EXT )
                    if target == target_:
                        target = os.path.join(path, '%i' % line.start + '_' + SNIPPET_EXT )

                    line.audio = target
                    line.save()
                    command += [
                        '-ss', '%.2f' % (line.start - SNIPPET_MARGIN_BEFORE),
                        '-t', '%.2f' % (line.duration + SNIPPET_MARGIN_BEFORE +
                                        SNIPPET_MARGIN_AFTER),
                        '-vn',
                        '-ac', '1',
                        _full_path(target),
                    ]

                subprocess.check_output( command )

            movie.skip_snippet = True
            movie.save()


def extract_pitches():
    for movie in Movie.select().where(
            Movie.skip_line == True,
            Movie.skip_snippet == True,
            Movie.skip_pitch == False):

        print "Extracting pitches for '%s'" % movie.title

        bar = progressbar.ProgressBar()
        for line in bar( movie.lines.where(Line.pitch == None) ):
            with db.transaction():

                try:
                    signal = basic.SignalObj( _full_path(line.audio) )
                    pitch = pYAAPT.yaapt(signal)

                    t = pitch.frames_pos / signal.fs

                    # Gaussian filter
                    kern = sg.gaussian(20, 2)
                    lp = sg.filtfilt( kern, np.sum(kern), pitch.samp_interp )
                    lp[ pitch.samp_values == 0 ] = np.nan

                    line.pitch = np.vstack( (t, lp) )
                except Exception:
                    line.pitch = None

                line.save()

        movie.skip_pitch = True
        movie.save()


def analyze_pitches():
    for movie in Movie.select().where(
            Movie.skip_line == True,
            Movie.skip_snippet == True,
            Movie.skip_pitch == True):

        print "Analyzing pitches for '%s'" % movie.title

        bar = progressbar.ProgressBar()
        for line in bar( movie.lines.where(Line.sextimate == None,
                                           Line.pitch != False)):
            with db.transaction():

                if line.pitch is None:
                    print "No pitch for Line %i in '%s'. Skip.." % (line.start, line.movie.title)
                    continue

                try:
                    p = line.pitch[1, :]
                    kde = st.gaussian_kde( p[~np.isnan(p)] )
                    locs = np.linspace(50, 400, 100)
                    vals = kde.evaluate(locs)

                    peak = locs[ np.argmax(vals) ]
                    line.sextimate = peak

                except Exception:
                    print "Exception during analysis for line at second %i." % line.start
                    line.sextimate = False

                line.save()


def _full_path(target):
    return os.path.join(movies_dir, target)

if __name__ == '__main__':
    # parse_args()
    rescan_dir()
    create_lines()
    create_snippets()
    extract_pitches()
    analyze_pitches()

    os.system('say "Filme fertig verarbeitet!"')
