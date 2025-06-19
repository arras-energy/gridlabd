"""Forecast data access

Syntax: gridlabd forecast [OPTIONS ...] COMMAND [ARGUMENTS ...]

Options:

Commands:

The `forecast` tool provides access to recent and archived numerical weather
prediction model outputs from different cloud archive sources delivered by
Herbie. 

See also:
* https://github.com/blaylockbk/Herbie
"""

import os
import sys
from herbie import Herbie

E_OK = 0
E_SYNTAX = 1

def main(argv):

    if len(argv) == 0:

        print("\n".join([x for x in __doc__ if x.startswith("Syntax: ")]))
        exit(E_SYNTAX)


if __name__ == "__main__":
    try:
        main(sys.argv)
        exit(E_OK)
    except Exception as err:
        e_type,e_name,e_trace = sys.exc_info()
        if DEBUG:
            raise
        exception(err)

