import os
import peewee as pw
from playhouse.fields import PickledField
from sqlite3 import OperationalError
#from playhouse.sqlite_ext import FTS5Model, SearchField


def connect(path):
    db = pw.SqliteDatabase(path)

    class Movie(pw.Model):
        title = pw.TextField(unique=True)
        subtitles = pw.TextField()
        video = pw.TextField()

        framerate = pw.TextField(null=True)
        width = pw.IntegerField(null=True)
        height = pw.IntegerField(null=True)
        total_duration = pw.FloatField(null=True)

        class Meta:
            database = db

        skip_line = pw.BooleanField(default=False)
        skip_snippet = pw.BooleanField(default=False)
        skip_pitch = pw.BooleanField(default=False)
        skip_analysis = pw.BooleanField(default=False)

    class Line(pw.Model):
        movie = pw.ForeignKeyField(Movie, related_name='lines', index=True)
        start = pw.FloatField(index=True)  # seconds
        duration = pw.FloatField()  # "

        text = pw.TextField()

        audio = pw.TextField(default=None, null=True)  # path to audio snippet
        pitch = PickledField(default=None, null=True)  # pitch array

        pitch_peak = pw.FloatField(default=None, null=True)
        sextimate = pw.FloatField(default=None, null=True)  # sex estimate

        class Meta:
            primary_key = pw.CompositeKey('movie', 'start')
            database = db


    db.connect()

    if not Movie.table_exists() and not Line.table_exists():
        db.create_tables([Movie, Line])

    return db, Movie, Line


'''
class LineIndex(FTS5Model):
    text = SearchField()

    class Meta:
        database = db
        extension_options = {'text': Line.text}

'''
