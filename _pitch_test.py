#!/usr/bin/env python

import sys

from schema import Line
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sg
from scipy import stats as st

plt.style.use('ggplot')

import amfm_decompy.pYAAPT as pYAAPT
import amfm_decompy.basic_tools as basic

lines = Line.select().where(Line.id << sys.argv[1:])

for line in lines:
    signal = basic.SignalObj( line.audio )
    pitch = pYAAPT.yaapt(signal)

    t = pitch.frames_pos / signal.fs
    p = pitch.samp_interp
    p[p==0] = np.nan

    fig, (a,b) = plt.subplots(1, 2, sharey=True, 
                              num="#%i: " % (line.id) \
                                 + line.text.replace('\n', ' '),
                              figsize=(10,5),
                              )

    #a.plot(t, p, lw=1)
    a.set_ylim(50, 400)
    a.set_xlim(right=np.max(t))

    kern = sg.gaussian(20, 2)
    lp = sg.filtfilt( kern, np.sum(kern), p )
    lp[ pitch.samp_values==0 ] = np.nan
    a.plot(t, lp, lw=2)

    a.set_ylabel('f0 estimate / Hz')
    a.set_xlabel('time / s')
    b.set_xlabel('density estimate')

    # This is only meaningful as long as the signal is equidistantly sampled!
    '''
    bins, edges, _ = b.hist(lp, 20, (50,400), 
                            orientation='horizontal', 
                            normed=True,
                            )

    centers = (edges[1:] + edges[:-1])/2

    hmax = centers[np.argmax(bins)]
    '''


    kde = st.gaussian_kde( lp[~np.isnan(lp)] )
    locs = np.linspace(50, 400, 200)
    vals = kde.evaluate(locs)

    b.fill_between( vals, locs )
    hmax = locs[ np.argmax(vals) ]
    
    median = np.nanmedian( lp )

    b.set_title('med: %.1f, peak: %.1f' % (median, hmax))
    a.set_title(line.text.replace('\n', ' '))

    fig.show()
    fig.tight_layout()


raw_input("Press Enter to close")
