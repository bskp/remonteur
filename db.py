import peewee as pw

db = pw.SqliteDatabase('lines.db')

class Movie(pw.Model):
    title = pw.TextField(unique=True)
    subtitles = pw.TextField()
    video = pw.TextField()

    class Meta:
        database = db

    lines_complete = pw.BooleanField(default=False)
    snippets_complete = pw.BooleanField(default=False)
    pitches_complete = pw.BooleanField(default=False)


class Line(pw.Model):
    text = pw.TextField()

    movie = pw.ForeignKeyField(Movie, related_name='lines')
    start = pw.FloatField() # seconds
    duration = pw.FloatField() # "

    audio = pw.TextField(default=None, null=True) # path to audio snippet
    pitch = pw.BlobField(default=None, null=True) # pitch array
    femaleness = pw.FloatField(default=None, null=True) # gender estimate between 0 and 1

    class Meta:
        database = db # This model uses the "people.db" database.

db.connect()
