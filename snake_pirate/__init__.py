import rpy2.robjects as robjects
import pandas as pd
import pandas.rpy.common as rcom

import snake_pirate.conversion as rconv
import snake_pirate.rplot as rplot
import snake_pirate.to_py 

def tz_warning():
    """
        This keeps on catching me
    """
    r_tz = robjects.r('Sys.getenv("TZ")')[0]
    if r_tz == "":
        print "=============WARNING==================="
        print "R Sys TZ is not set. This can get hazardous for your sanity."
        print "Set to your data's TZ or GMT for pandas tz-naive data"
        print "Sys.setenv(TZ='GMT')"
        print "=============WARNING==================="

robjects.conversion.ri2py = robjects.default_ri2py

tz_warning()
# Probably need better logic to detect if xts was imported
robjects.r('require(xts)')
rplot.patch_call()

def pd_py2ri(o):
    """ 
    Pandas based conversion
    """
    res = None
    if isinstance(o, pd.Series): 
        o = pd.DataFrame(o, index=o.index)

    if isinstance(o, pd.DataFrame): 
        if isinstance(o.index, pd.DatetimeIndex):
            res = rconv.convert_df_to_xts(o)
        else:
            res = rcom.convert_to_r_dataframe(o)

    if isinstance(o, pd.DatetimeIndex): 
        res = rconv.convert_datetime_index(o)

    if isinstance(o, pd.Timestamp): 
        res = rconv.convert_timestamp(o)
        
    if res is None:
        res = robjects.default_py2ri(o)

    return res

robjects.conversion.py2ri = pd_py2ri

# new r object.
class R(object):
    def __init__(self):
        pass

    def __getattr__(self, key):
        if hasattr(robjects.r, key):
            return getattr(robjects.r, key)
        raise AttributeError()

    def __call__(self, *args, **kwargs):
        return robjects.r(*args, **kwargs)

    def __getitem__(self, key):
        return robjects.r[key]

    def __setitem__(self, key, val):
        robjects.r.assign(key, val)

r = R()
r.NULL = robjects.NULL
