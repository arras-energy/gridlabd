"""Regression testing analysis

Syntax: `gridlabd python [OPTIONS ...] utilities/regression.py BEFORECSV AFTERCSV`

where `BEFORECSV` and `AFTERCSV` are obtained using the commands

    gridlabd --validate=BEFORECSV
    # make your changes
    gridlabd --validate=AFTERCSV

Options
-------

    `-d|--debug`                 enable debug traceback on exception
    
    `-h|--help|help`             display this documentation

    `--sortby=FIELD`             sort output by FIELD (use `-FIELD` to reverse
                                 sort)
    
    `--ignore`                   ignore failed autotests and mismatched
                                 autotest names

    `-o|--output=[FILE].FORMAT   specify output file and format

If omitted, the default input files are `before.csv` and `after.csv`,
respectively.

The following output formats are supported:

    `.csv`    CSV file with header

    `.json`   JSON file

    `.txt`    Pandas dataframe table

If the output file is not specified then output is sent to `/dev/stderr`.

Output may be sorted using the `--sortby=FIELD` option. Supported fields are

  - `autotest`              the name of the autotest
  - `before[s]`             the autotest timing before the change
  - `after[s]`              the autotest timing after the change
  - `absolute_change[s]`    the absolute change in the timing
  - `relative_change[%]`    the relative change in the timing

Python usage
------------

You may call the regression using the `main()` function as follows:

    import sys
    sys.path.append("utilities")
    import regression
    main(OPTIONS,...,BEFORECSV,AFTERCSV)

See Also
--------

* [/Command/Validate]
"""

import os
import sys
import pandas as pd

SORTBY = "autotest"
DEBUG = False
IGNORE = False
BEFORECSV = "before.csv"
AFTERCSV = "after.csv"
OUTPUT = None

pd.options.display.max_rows = None

def main(*args):

    args = list(args)

    if len(args) > 1 and args[1] in ["-h","--help","help"]:
        print(__doc__)
        exit(0)

    for arg in [x for x in args if x.startswith('-')]:


        if arg in ["-d","--debug"]:
            global DEBUG
            DEBUG = True
        elif arg.startswith("--sortby="):
            global SORTBY
            SORTBY = arg.split("=",1)[1]
        elif arg in ["--ignore"]:
            global IGNORE
            IGNORE = True
        elif arg.startswith("-o=") or arg.startswith("--output="):
            global OUTPUT
            OUTPUT = arg.split("=",1)[1]
        else:
            raise Exception(f"option '{arg}' is invalid")
        args.remove(arg)

    if len(args) > 1: 

        global BEFORECSV
        BEFORECSV = args[1]

    if len(args) > 2:

        global AFTERCSV
        AFTERCSV = args[2]

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

    return result[result["before[s]"]>0].sort_values(SORTBY.strip('-'),ascending=SORTBY[0]!='-').set_index('autotest')

if __name__ == "__main__":

    try:

        result = main(*sys.argv)
        if OUTPUT is not None and OUTPUT[0] == '.':
            ext = OUTPUT
            OUTPUT = "/dev/stdout"
        else:
            ext = os.path.splitext(OUTPUT)[1] if OUTPUT else None
        if OUTPUT is None:
            print(result)
        elif ext == ".csv":
            result.to_csv(OUTPUT)
        elif ext == ".json":
            result.to_json(OUTPUT)
        elif ext == ".txt":
            with open(OUTPUT,"w") as fh:
                print(result,file=fh)
        else:
            raise Exception(f"output format '{ext}' if not supported")

        exit(0)

    except Exception as err:

        if DEBUG:
            raise

        print("ERROR [regression]:",err,file=sys.stderr)

        exit(1)