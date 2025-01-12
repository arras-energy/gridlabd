"""Add meters from CSV table

Syntax: gridlabd add_meters JSONFILE CSVFILE [OPTIONS ...]

Options:

* `--limit=DISTANCE`: ignore transformers more than DISTANCE feet from any
  meter.

* `--id[=NAME]`: specify the meter field name to use for identifying
  transformers. If none is specified, the default field name "id" is ignored.

* `--missing=[ignore|warn|fail]`: specify what to do when a meter has no
  transformer.

Description:

The `add_meters` command loads the model in JSONFILE and adds the meters
listed in CSVFILE. Two methods of identifying where meters are connected are
allowed:

1. **Nearest service transformer**: The service transformers and the meters
must have latitude and longitude values specified. Each meter is connected to
nearest service transformer provided it is within DISTANCE feet of the
meter.

2. **Service transformer name**: The service transformers are identified
explicitly by the meter. If a meter is more than DISTANCE feet from the meter
a warning is printed to stderr.


"""

import sys
import os
import framework as app

def main(argv):

    DISTANCE = 1000.0 # ft
    NAME = "id" # default transformer id field name in meter records

    args = read_stdargs(argv)

    for key,value in args:

        if key in ["-h","--help","help"]:
            print(__doc__,file=sys.stdout)

        elif key in ["--limit"]:

            DISTANCE = float(value)

        elif key in ["--id"]:

            NAME = value

        else:
            error(f"'{key}={value}' is invalid")
            return app.E_INVALID

    model = json.load(open(argv[1],"r"))
    meters = pd.read_csv(argv[2])

    return app.E_OK

if __name__ == "__main__":

    try:

        if len(sys.argv) == 1:
            glmfile = f"test_{os.path.splitext(os.path.basename(__file__))[0]}.glm"
            glmpath = os.path.join(os.path.dirname(__file__),"autotest")
            if os.path.exists(os.path.join(glmpath,glmfile)) \
                    and os.getcwd() == os.path.dirname(__file__) \
                    and "GLD_BIN" in os.environ:
                app.warning(f"running autotest file refresh {glmfile}...")
                rc = os.system(f"gridlabd.bin -W {glmpath} {glmfile}")
                exit(rc)
            else:
                print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]),file=sys.stderr)
                exit(app.E_SYNTAX)
            fi

        rc = main(sys.argv)
        exit(rc)

    except KeyboardInterrupt:

        exit(app.E_INTERRUPT)

    except Exception as exc:

        if DEBUG:
            raise exc

        if not QUIET:
            e_type,e_value,e_trace = sys.exc_info()
            tb = traceback.TracebackException(e_type,e_value,e_trace).stack[1]
            print(f"EXCEPTION [{app.EXEFILE}@{tb.lineno}]: ({e_type.__name__}) {e_value}",file=sys.stderr)

        exit(app.E_EXCEPTION)