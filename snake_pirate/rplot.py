"""
Enable ipython plotting without requiring the use of rmagic

This entails a two step process.

1. `plot_to_tempdir`: setup R to start writing plots out to a tempdir with `png`
2. `process_plots`: Read all the images from the directory and plot them into matplotlib.
3. `matplotlib` takes it over from there. IPython has native support for mpl so there's no more translation. 

Note: I chose to route the R.plots to `matplotlib` instead of creating ipython display
primatives. It seemed like the simplest way to quickly offload responsibility to more
stable workflows. Everyone interfaces with mpl, so there's no extra work after that pointEveryone interfaces with mpl, so there's no extra work after that point.
"""
import tempfile
from glob import glob
from shutil import rmtree

import matplotlib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import rpy2.robjects as robjects
r = robjects.r
png = r['png']

RPLOT_CONTEXT = None

_get_figsize = lambda: matplotlib.rcParams['figure.figsize']
_get_dpi = lambda: matplotlib.rcParams['figure.dpi']

def plot_to_tempdir(width=None, height=None, dpi=None):
    """
        Start writing R plots to temp_dir via png
    """
    if width is None or height is None:
        width, height = _get_figsize()
    if dpi is None:
        dpi = _get_dpi()

    temp_dir = tempfile.mkdtemp()
    filemask = "%s/Rplots%%03d.png" % (temp_dir)
    png(filemask, width=width, height=height, units='in', res=dpi, pointsize=34)
    return temp_dir

def process_plots(temp_dir):
    """
        Take all rplots in temp_dir and plot them via matplotlib
    """
    r('dev.off()')

    images = [mpimg.imread(imgfile) for imgfile in glob("%s/Rplots*png" % temp_dir)]
    for image in images:
        plot_image(image)

    if images:
        print 'RPlot processed {count} images'.format(count=len(images))
    plt.show()
    rmtree(temp_dir)

def plot_image(image):
    """
        Take a matplot image file and plots it to a new
        figure with minimal decoration. (no borders, axes)
    """
    fig = plt.figure(frameon=False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.imshow(image)

class RPlot(object):
    """
    ContextManager wrapper around plot_to_tempdir
    and process_plots
    """
    def __init__(self):
        self.temp_dir = None

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        self.end()

    def start(self):
        self.temp_dir = plot_to_tempdir()

    def end(self):
        process_plots(self.temp_dir)

def wrapped_call(self, *args, **kwargs):
    """
        Wraps around Function.__call__ to enable
        RPlotting. 
        #TODO There has to be a better way to do this.
    """
    global RPLOT_CONTEXT
    # within context short-circuit
    if RPLOT_CONTEXT is not None:
        res = self.__base_call__(*args, **kwargs)
        return res

    if RPLOT_CONTEXT is None:
        RPLOT_CONTEXT = RPlot()
        RPLOT_CONTEXT.start()

    res = self.__base_call__(*args, **kwargs)

    if RPLOT_CONTEXT is not None:
        RPLOT_CONTEXT.end()
        RPLOT_CONTEXT = None
    return res

def patch_call():
    """
        Wrap around the Function call to enable rplot -> matplotlib
    """
    if hasattr(robjects.Function, '__base_call__'):
        return
    robjects.Function.__base_call__ = robjects.Function.__call__
    robjects.Function.__call__ = wrapped_call
