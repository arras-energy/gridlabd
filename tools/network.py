"""Network data analysis and extraction

Syntax: gridlabd network OPTIONS [...]

OPTIONS
    -h|--help|help              get this help
    -i|--input[=[FILEPATH]]     set input file (default stdin)
    -o|--output[=[FILEPATH]]    set output file (default stdout)
    -t|--filetype[=[FILETYPE]]  set file type (default 'auto')
    -z|--zero=FLOAT             set near zero value (default 1e-12)
    -p|--precision=INTEGER      set output decimal precision (default 4)
    -g|--generator=SCHEME       add swing bus generators (default 'auto')

DESCRIPTION

Input JSON file must be a valid GridLAB-D JSON model which includes objects.

Output can be a JSON or a PyPower case. JSON files are used for 'network'
filetype and contains the 3-phase network topology data, including

        N = number of busses
        M = number of branches
        Z = branch impedances
        R = branch resistances
        row = row index
        col = col index
        A = unweighted Laplacian matrix
        I = weighted line-node incidence matrix
        L = weighted Laplacian matrix
        J = incidence matrix,

Output can also be a 'pypower' filetype for a PyPower case data. See 
pypower.org for information on the format of PyPower case data.

The `zero` option is used to set the near-zero value to avoid divide-by-zero
errors when calculating the line impedances. The `precision` value is used to
set the output data decimal precision.

The `generator` option is used to determine whether and how the swing bus
generator is defined. The following values are recognized:

    auto        automatically add a generator if none is found on a swing bus 
    single      consolidate swing bus generators even if the swing busses appear to be separate
    none        do not add generators to swing busses
    multiple    separate swing bus generators even if the swing busses appear to be the same

"""

import os, sys, json, signal
import numpy as np
import scipy as sp

np.set_printoptions(linewidth=np.inf,precision=4,floatmode='maxprec',suppress=True,threshold=sys.maxsize)

EXEPATH = sys.argv[0]
EXENAME = os.path.basename(EXEPATH)

WARNING=not "--warning" in sys.argv
QUIET="--quiet" in sys.argv
VERBOSE="--verbose" in sys.argv
DEBUG="--debug" in sys.argv

E_OK = 0
E_INVALID = 1
E_INTERRUPT = 2
E_FAILED = 3
E_SYNTAX = 8
E_EXCEPTION = 9

PRECISION=4
NEARZERO=1e-12
GENERATOR='auto'

def exception(*args,**kwargs):
    if not QUIET:
        e_name,e_value,e_trace=sys.exc_info()
        for key,value in dict(end="\n",flush=True,file=sys.stderr).items():
            if not key in kwargs:
                kwargs[key] = value
        msg = f"EXCEPTION [{EXENAME}@{e_trace.tb_lineno}]: ({e_name.__name__}) {e_value}"
        print(msg,**kwargs)
    error(E_EXCEPTION,*args,**kwargs)

def error(code:int,*args,**kwargs):
    if not QUIET:
        for key,value in dict(end="\n",flush=True,file=sys.stderr).items():
            if not key in kwargs:
                kwargs[key] = value
        msg = f"ERROR [{EXENAME}]: {' '.join([str(x) for x in args])}"
        if type(code) is int:
            msg += f" (code {code})"
        print(msg,**kwargs)
    if type(code) is int:
        exit(code)

def warning(*args,**kwargs):
    if WARNING:
        for key,value in dict(end="\n",flush=True,file=sys.stderr).items():
            if not key in kwargs:
                kwargs[key] = value
        msg = f"WARNING [{EXENAME}]: {' '.join([str(x) for x in args])}"
        print(msg,**kwargs)

def verbose(*args,**kwargs):
    if VERBOSE:
        for key,value in dict(end="\n",flush=True,file=sys.stderr).items():
            if not key in kwargs:
                kwargs[key] = value
        msg = f"VERBOSE [{EXENAME}]: {' '.join([str(x) for x in args])}"
        print(msg,**kwargs)

INPUTPATH="/dev/stdin"
INPUTFILE=sys.stdin
OUTPUTPATH="/dev/stdout"
OUTPUTFILE=sys.stdout
FILETYPE='auto'

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (complex)):
            return f"{obj.real}{obj.imag:+f}j"
        else:
            return super().default(obj)

def get_powerflow_network(objects):
        # extract branch information
        branches = {name:data for name,data in objects.items() if "from" in data and "to" in data}

        # extract bus information
        buses = {name:objects[name] for name in list(set([data["from"] for data in branches.values()] + [data["to"] for data in branches.values()]))}
        bus = np.full((3,len(buses),13),float('nan'))
        bus_i,busnames = zip(*enumerate(buses.keys()))
        busmap = {value:key for key,value in enumerate(busnames)}
        bus[0,:,0] = np.array(bus_i) + 1
        bus[1,:,0] = bus[0,:,0] + bus.shape[1]
        bus[2,:,0] = bus[1,:,0] + bus.shape[1]
        btmap = {"PQ":1,"PV":2,"SWING":3,"PQREF":3}
        nominal_voltages = np.array([[float(value.split()[0]) for key,value in buses[name].items() if key == f"nominal_voltage"][0] for name in busnames])
        for m,p in enumerate("ABC"):
            bus[m,:,1] = [btmap[x["bustype"]] for x in buses.values()]
            bus[m,:,2] = [sum([float(value.split()[0])/1e6 for key,value in buses[name].items() if key == f"constant_power_{p}_real"]) for name in busnames]
            bus[m,:,3] = [sum([float(value.split()[0])/1e6 for key,value in buses[name].items() if key == f"constant_power_{p}_reac"]) for name in busnames]
            voltages = np.array([[complex(value.split()[0]) for key,value in buses[name].items() if key == f"voltage_{p}"][0] for name in busnames])
            bus[m,:,7] = np.abs(voltages) / nominal_voltages
            bus[m,:,8] = np.angle(voltages) * 180 / np.pi
            bus[m,:,9] = nominal_voltages
        bus[:,:,4] = 0.0 # shuft G
        bus[:,:,5] = 0.0 # shunt B
        bus[:,:,6] = 1.0 # baseKV
        bus[:,:,10] = 1.0 # loss zone
        bus[:,:,11] = 1.2
        bus[:,:,12] = 0.8
        bus = bus.reshape(bus.shape[0]*bus.shape[1],bus.shape[2])
        N = bus.shape[0]
        verbose(f"N = {N}")
        verbose(f"bus ({'x'.join([str(x) for x in bus.shape])}) =\n{bus}")

        branch_i,branchnames = zip(*enumerate(branches.keys()))
        branch = np.full((3,len(branches),13),float('nan'))
        branch[0,:,0] = np.array([[busmap[z] for y,z in x.items() if y == "from"] for x in branches.values()]).transpose()+1 # from
        branch[1,:,0] = branch[0,:,0] + N/3
        branch[2,:,0] = branch[1,:,0] + N/3
        branch[0,:,1] = np.array([[busmap[z] for y,z in x.items() if y == "to"] for x in branches.values()]).transpose()+1 # to
        branch[1,:,1] = branch[0,:,1] + N/3
        branch[2,:,1] = branch[1,:,1] + N/3
        losses = np.array([[complex(z.split()[0]) for y,z in x.items() if y.startswith("power_losses_")] for x in branches.values()]).transpose()
        currents = np.array([[complex(z.split()[0]) for y,z in x.items() if y.startswith("current_in_")] for x in branches.values()]).transpose()
        voltages = losses / (currents.conjugate()+NEARZERO)
        impedances = voltages / (currents+NEARZERO)
        for p in range(3):
            branch[p,:,2] = impedances[p].real # R_p
            branch[p,:,3] = impedances[p].imag # X_p
        branch[0,:,4] = 1 / ( branch[0,:,3] + NEARZERO) # B_0
        branch[1,:,4] = 1 / ( branch[1,:,3] + NEARZERO) # B_1
        branch[2,:,4] = 1 / ( branch[2,:,3] + NEARZERO) # B_2
        branch[0,:,6] = branch[1,:,6] = branch[2,:,6] = branch[0,:,5] = branch[1,:,5] = branch[2,:,5] = np.array([[float(z.split()[0]) for y,z in x.items() if y == "continuous_rating"] for x in branches.values()]).transpose()
        branch[0,:,7] = branch[1,:,7] = branch[2,:,7] = np.array([[float(z.split()[0]) for y,z in x.items() if y == "emergency_rating"] for x in branches.values()]).transpose()
        branch[0,:,8] = branch[1,:,8] = branch[2,:,8] = 1.0 # tap ratios
        branch[0,:,9] = branch[1,:,9] = branch[2,:,9] = 0.0 # phase shifts
        branch[:,:,10] = (currents!=0) # status
        branch[0,:,11] = branch[1,:,11] = branch[2,:,11] = -360
        branch[0,:,12] = branch[1,:,12] = branch[2,:,12] = +360
        branch = branch.reshape(branch.shape[0]*branch.shape[1],branch.shape[2])
        M = branch.shape[0]
        verbose(f"M = {M}")
        verbose(f"branch ({'x'.join([str(x) for x in branch.shape])}) =\n{branch}")

        global FILETYPE
        if FILETYPE == "auto":
            ext = os.path.splitext(OUTPUTPATH)[1][1:]
            try:
                FILETYPE = dict(json="network",py="pypower")[ext]
            except KeyError:
                error(E_INVALID,f"no known filetype for extension '{ext}'")

        if FILETYPE == "network":

            # impedance values
            Z = np.array([complex(*x) for x in zip(branch.T[2],branch.T[3])])
            verbose(f"Z ({'x'.join([str(x) for x in Z.shape])}) =",Z)

            # # Real impedance by line
            R = branch.T[2]

            # get A - Laplacian matrix
            row = [int(x)-1 for x in branch[:,0]]
            col = [int(x)-1 for x in branch[:,1]]
            assert(len(row)==M)
            assert(len(col)==M)
            verbose(f"row ({len(row)}) =",row)
            verbose(f"col ({len(col)}) =",col)
            A = sp.sparse.coo_array(([1]*M + [-1]*M,(row+col,col+row)),(N,N))
            verbose(f"A  ({'x'.join([str(x) for x in A.shape])}) =\n{A.toarray()}")

            # get I - weighted line-node incidence matrix
            I = sp.sparse.coo_array((Z,(list(range(M)),row)),shape=(M,N)) - sp.sparse.coo_array((Z,(list(range(M)),col)),shape=(M,N))
            verbose(f"I  ({'x'.join([str(x) for x in I.shape])}) =\n{I.toarray()}")

            # get L - weighted Laplacian
            L = I.T@I
            verbose(f"L =\n{L.toarray()}")

            J = adjacency_to_incidence(A)
            verbose(f"J =\n{J}")

            busphases = [x+"_A" for x in busnames]+[x+"_B" for x in busnames]+[x+"_C" for x in busnames]
            branchphases = [x+"_A" for x in branchnames]+[x+"_B" for x in branchnames]+[x+"_C" for x in branchnames]
            return dict(
                N = N,
                M = M,
                line={x:[int(y) for y in branch[n,0:2]] for n,x in enumerate(branchphases)},
                Z = Z.round(PRECISION),
                R = R.round(PRECISION),
                row = [busphases[x] for x in row],
                col = [busphases[x] for x in col],
                A = A.toarray().round(PRECISION),
                I = I.toarray().round(PRECISION),
                L = L.toarray().round(PRECISION),
                J = J.toarray().round(PRECISION),
                )

        elif FILETYPE == "pypower":

            return f"""from numpy import array

def {os.path.splitext(os.path.basename(OUTPUTPATH))[0]}():
    return dict(
        version=2,
        baseMVA=100.0,
        bus=array({bus.round(PRECISION)}),
        branch=array({branch.round(PRECISION)}),
        gen=array([]),
        gencost=array([]),
    )
"""


def adjacency_to_incidence(A: sp.sparse.spmatrix) -> sp.sparse.spmatrix:
    """
    Args:
        A: adjacency matrix, sp.sparray of shape N x N

    Returns:
        I: incidence matrix, sp.sparray of shape N x M
    """

    assert (A + A.T).nnz == 0, "Expected undirected graph."
    assert np.all(A.diagonal() == 0), "Expected no self-loops."

    mask = A.row > A.col

    N = A.shape[0]
    M = np.sum(mask, dtype=int)

    data = np.concatenate([np.ones(M), -np.ones(M)])
    row = np.concatenate([A.row[mask], A.col[mask]])
    col = np.concatenate([np.arange(M), np.arange(M)])

    return sp.sparse.coo_matrix((data, (row, col)), shape=(N, M))

if __name__ == "__main__":

    if len(sys.argv) == 1:
        print("\n".join([x for x in __doc__.split("\n") if x.startswith("Syntax: ")]),file=sys.stderr)
        exit(E_SYNTAX)

    try:
        for arg in sys.argv[1:]:
            key,value = arg.split("=") if "=" in arg else (arg,None)
            if key == "-":
                pass
            elif key in ["-h","--help","help"]:
                print(__doc__,file=sys.stdout)
                exit(E_OK)
            elif key in ["--verbose"]:
                VERBOSE=True
            elif key in ["--debug"]:
                DEBUG=True
            elif key in ["--quiet"]:
                QUIET=True
            elif key in ["--warning"]:
                VERBOSE=False
            elif key in ["-i","--input"]:
                INPUTPATH=value if value else "/dev/stdin"
                INPUTFILE=open(value,"r") if value else sys.stdin
            elif key in ["-o","--output"]:
                OUTPUTPATH=value if value else "/dev/stdout"
                OUTPUTFILE=open(value,"w") if value else sys.stdout
            elif key in ["-t","--filetype"] and value in ["network","pypower"]:
                FILETYPE=value if value else "auto"
            elif key in ["-z","--zero"]:
                try:
                    NEARZERO=float(value)
                    assert NEARZERO>0, "zero value must be strict positive"
                except ValueError:
                    error(E_INVALID,f"'{arg}' has an invalid float value")
                except AssertionError:
                    error(E_INVALID,f"'{arg}' value must be strictly positive")
            elif key in ["-p","--precision"]:
                try:
                    PRECISION=int(value)
                except ValueError:
                    error(E_INVALID,f"'{arg}' has an invalid integer value")
            else:
                error(E_INVALID,f"option '{arg}' is invalid")

        DATA=json.load(INPUTFILE)
        if not "application" in DATA or DATA["application"] != "gridlabd":
            error(E_INVALID,"input is not a valid gridlbad JSON model")
        if not "modules" in DATA or not "powerflow" in DATA["modules"]:
            error(E_FAILED,"JSON model does not reference the powerflow module")
        if not "objects" in DATA or not DATA["objects"]:
            error(E_FAILED,"JSON model contains no object data")
        results = get_powerflow_network(DATA["objects"])
        if type(results) is dict:
            print(json.dumps(results,indent=4,cls=NumpyEncoder),file=OUTPUTFILE) 
        elif type(results) is str:
            print(results,file=OUTPUTFILE)
        else:
            exception("get_powerflow_network() returned an invalid result type")


    except SystemExit:

        pass

    except:

        if DEBUG:
            raise
        exception("command failed")

    exit(E_OK)
