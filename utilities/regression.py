"""Regression testing analysis

Syntax: `gridlabd python [OPTIONS ...] utilities/regression.py before.csv after.csv`

where `before.csv` and `after.csv` are obtained using the commands

    gridlabd --validate=before.csv
    # make your changes
    gridlabd --validate=after.csv

Options:

    `-d|--debug`          enable debug traceback on exception
    `-h|--help|help`      display this documentation
    `--sortby=FIELD`      sort output by FIELD (use `-FIELD` to reverse sort)
    `-i|--ignore`         ignore failed autotests and mismatched autotest names

If omitted, the default files are `before.csv` and `after.csv`, respectively.
"""

import os
import sys
import pandas as pd

SORTBY = "autotest"
DEBUG = False
IGNORE = False
BEFORECSV = "before.csv"
AFTERCSV = "after.csv"

pd.options.display.max_rows = None

if __name__ == "__main__":

    try:

        if len(sys.argv) > 1 and sys.argv[1] in ["-h","--help","help"]:
            print(__doc__)
            exit(0)

        for arg in [x for x in sys.argv if x.startswith('-')]:


            if arg in ["-d","--debug"]:
                DEBUG = True
            elif arg.startswith("--sortby="):
                SORTBY = arg.split("=",1)[1]
            elif arg in ["-i","--ignore"]:
                IGNORE = True
            else:
                raise Exception(f"option '{arg}' is invalid")
            sys.argv.remove(arg)

        if len(sys.argv) > 1: 

            BEFORECSV = sys.argv[1]

        if len(sys.argv) > 2:

            AFTERCSV = sys.argv[2]

        before = pd.read_csv(BEFORECSV,index_col=0).sort_index()
        after = pd.read_csv(AFTERCSV,index_col=0).sort_index()

        if not IGNORE:
            assert (before.status=="OK").all(), f"{BEFORECSV}: not all tests passed"
            assert (after.status=="OK").all(), f"{AFTERCSV}: not all tests passed"
            assert (before.index==after.index).all(), "autotest index mismatched"

        result = pd.DataFrame({
            "before[s]":before.time,
            "after[s]":after.time,
            "absolute_change[s]":(after.time-before.time),
            "relative_change[%]":(after.time/before.time-1).round(3)*100},
            ).fillna(0)
        result.index = [x.replace(os.getcwd()+"/","") for x in result.index]
        result.index.name = "autotest"
        result.reset_index(inplace=True)
        
        assert SORTBY.strip('-') in result.columns, f"'{SORTBY}' is not a valid sort field"

        print(result[result["before[s]"]>0].sort_values(SORTBY.strip('-'),ascending=SORTBY[0]!='-').set_index('autotest'))

        exit(0)

    except Exception as err:

        if DEBUG:
            raise

        print("ERROR [regression]:",err,file=sys.stderr)

        exit(1)