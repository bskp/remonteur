#!/usr/bin/env python

import sys

import numpy as np
from scipy import signal as sg

from schema import Line, Movie

keywords = sys.argv[1:]

query = Line.select()
for keyword in keywords:
    query = query.where( Line.text.contains(keyword.replace('_', ' ') )  )

for line in query:
    print "%s #%i:\t'%s'" % (line.movie.title,
                              line.id,
                              line.text.replace('\n', ' '), 
                              )
