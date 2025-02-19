"""Timeseries tools"""

import sys
import datetime as dt
import pandas as pd
from typing import TypeVar

def project_daterange(source:list[TypeVar('datetime.datetime')],
    target:list[TypeVar('datetime.datetime')]=None,
    start:str|TypeVar('datetime.datetime')=None,
    end:str|TypeVar('datetime.datetime')=None,
    align:bool=None,
    ) -> dict:
    """Map dates to a new date range

    Arguments:

    * `source`: date/time series to map to

    * `target`: date/time series to map from

    * `align`: mapping alignment

    Returns:

    * `dict`: mapping from target to source

    Description:

    Maps dates from a target range to a source range using the alignment
    provided, if any.  Valid alignments are:

    * `None`: the mapping is based on the start date (e.g., simple wrapped map)
    
    * `'year'`: the mapping is based on the day of the year (day of year aligned)

    * `'week'`: the mapping is based on the day of week (day of week of year aligned)
    """
    if not start is None and not end is None:
        target = pd.date_range(start=start,end=end,freq=source.freq)
    if target is None:
        raise ValueError("either start and end or target range must be specified")
    fromlen = len(source)
    tolen = len(target)

    # TODO: set offset
    if align is None:
        offset = 0
    elif align == "year":
        offset = (target[0]-source[0]).days%365
    elif align == "week":
        offset = (target[0]-source[0]).days%364
    else:
        raise ValueError("align is not valid (must be None, 'year', or 'week')")
    offset *= 24
    ndx = [int((x+offset)%len(source)) for x in range(0,len(target))]
    # print("index =",ndx)
    # print("source[ndx] =",[source[x] for x in ndx])

    mapping = dict(zip(target,[source[x] for x in ndx]))
    # elif tolen < fromlen: # clip
    #     target = source[:tolen]
    # elif fromlen > tolen: # repeat last day
    #     target[:fromlen] = source
    #     target[fromlen:] = source[fromlen:] + dt.timedelta(days=1)

    return mapping

def test():

    source = pd.date_range(start="2018-01-01 00:00:00-08:00",end="2019-01-01 00:00:00-08:00",freq="1h")
    mapping = project_daterange(source,start="2020-08-01 00:00:00-08:00",end="2020-09-01 00:00:00-08:00",align=None)
    t0 = dt.datetime.strptime("2020-08-01 00:00:00-08:00","%Y-%m-%d %H:%M:%S%z")
    assert mapping[t0] == dt.datetime.strptime("2018-01-01 00:00:00-08:00","%Y-%m-%d %H:%M:%S%z"), "incorrect mapping of date alignment None"

    source = pd.date_range(start="2018-01-01 00:00:00-08:00",end="2019-01-01 00:00:00-08:00",freq="1h")
    mapping = project_daterange(source,start="2020-08-01 00:00:00-08:00",end="2020-09-01 00:00:00-08:00",align='year')
    t0 = dt.datetime.strptime("2020-08-01 00:00:00-08:00","%Y-%m-%d %H:%M:%S%z")
    assert mapping[t0] == dt.datetime.strptime("2018-08-02 00:00:00-08:00","%Y-%m-%d %H:%M:%S%z"), "incorrect mapping of date alignment year"

    source = pd.date_range(start="2018-01-01 00:00:00-08:00",end="2019-01-01 00:00:00-08:00",freq="1h")
    mapping = project_daterange(source,start="2020-08-01 00:00:00-08:00",end="2020-09-01 00:00:00-08:00",align='week')
    t0 = dt.datetime.strptime("2020-08-01 00:00:00-08:00","%Y-%m-%d %H:%M:%S%z")
    assert mapping[t0] == dt.datetime.strptime("2018-08-04 00:00:00-08:00","%Y-%m-%d %H:%M:%S%z"), "incorrect mapping of date alignmend week"

if __name__ == "__main__":

    if not sys.argv[0]:

        # self test
        test()

    else:

        raise Exception("timeseries has no command line")



