import json 
import os 
import subprocess
import sys, getopt
import datetime
import importlib, copy
from importlib import util


config = {"input":"py","output":"glm","type":["python","pypower"]}

def help():
    return """py2glm.py -i <inputfile> -o <outputfile> [options...]
    -c|--config              output converter configuration data
    -h|--help                output this help
    -i|--ifile FILENAME.     [REQUIRED] PY input file
    -o|--ofile FILENAME      GLM output file name
    -t|--type TYPE           type of input file (default "pypower" with
                             fallback to "python")
    -N|--name                do not autoname objects
"""

DATASPEC = {
    "bus" : {
        "bus_i": "{:.0f}",
        "type": "{:.0f}",
        "Pd": "{:g} MW",
        "Qd": "{:g} MVAr",
        "Gs": "{:g} MW",
        "Bs": "{:g} MVAr",
        "area": "{:.0f}",
        "Vm": "{:g} pu.kV",
        "Va": "{:g} deg",
        "baseKV": "{:g} kV",
        "zone": "{:.0f}",
        "Vmax": "{:g} pu.kV",
        "Vmin": "{:g} pu.kV",
    },
    "gen": {
        "bus": "{:.0f}",
        "Pg": "{:g} MW",
        "Qg": "{:g} MVAr",
        "Qmax": "{:g} MVAr",
        "Qmin": "{:g} MVAr",
        "Vg": "{:g} pu.kV",
        "mBase": "{:g} MVA",
        "status": "{:.0f}",
        "Pmax": "{:g} MW",
        "Pmin": "{:g} MW",
        "Pc1": "{:g} MW",
        "Pc2": "{:g} MW",
        "Qc1min": "{:g} MVAr",
        "Qc1max": "{:g} MVAr",
        "Qc2min": "{:g} MVAr",
        "Qc2max": "{:g} MVAr",
        "ramp_agc": "{:g} MW/min",
        "ramp_10": "{:g} MW",
        "ramp_30": "{:g} MW",
        "ramp_q": "{:g} MVAr/min",
        "apf": "{:g} pu",
    },
    "branch": {
        "fbus": "{:.0f}",
        "tbus": "{:.0f}",
        "r": "{:g} pu.Ohm",
        "x": "{:g} pu.Ohm",
        "b": "{:g} pu.S",
        "rateA": "{:g} MVA",
        "rateB": "{:g} MVA",
        "rateC": "{:g} MVA",
        "ratio": "{:g} pu",
        "angle": "{:g} deg",
        "status": "{:.0f}",
        "angmin": "{:g} deg",
        "angmax": "{:g} deg",
    }
}
MODIFY = {
    "gen" : {
        "parent":("bus",lambda x:f"pp_bus_{int(x[0])}"),
        },
    "branch": {
        "from":("fbus",lambda x:f"pp_bus_{int(x[0])}"),
        "to":("tbus",lambda x:f"pp_bus_{int(x[1])}"),
    }
}

def main():
    filename_py = None
    filename_glm = None
    py_type = 'pypower'
    autoname = True
    try : 
        opts, args = getopt.getopt(sys.argv[1:],
            "chi:o:t:N",
            ["config","help","ifile=","ofile=","type=","name"],
            )
    except getopt.GetoptError:
        sys.exit(2)
    if not opts : 
        print('ERROR [py2glm.py]: missing command arguments')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c","--config"):
            print(config)
            sys.exit()
        elif opt in ("-h","--help"):
            print(help())
            sys.exit()
        elif opt in ("-i", "--ifile"):
            filename_py = arg
        elif opt in ("-o", "--ofile"):
            filename_glm = arg
        elif opt in ("-t", "--type"):
            py_type = arg
        elif opt in ("-N","--name"):
            autoname = False
        else : 
            print(f"ERROR [py2glm.py]: {opt}={arg} is not a valid option")
            sys.exit(1)

    if not filename_py:
        print(f"ERROR [py2glm.py]: input filename not specified")
        sys.exit(1)

    try:
        return convert(
            ifile = filename_py,
            ofile = filename_glm,
            options = dict(
                py_type = py_type,
                autoname = autoname),
            )
    except Exception as err:
        print(f"ERROR [py2glm.py]: {err}")
        import traceback
        traceback.print_exception(err,file=sys.stderr)
        sys.exit(9)

def convert(ifile,ofile,options={}):
    """Default converter is pypower case"""

    py_type = options['py_type'] if 'py_type' in options else "python"
    autoname = options['autoname'] if 'autoname' in options else True

    if not py_type in converters:
        raise ValueError(f"'type={py_type}' is not a valid conversion type")

    return converters[py_type](ifile,ofile,options)

def convert_python(ifile,ofile,options={}):
    """Run python script"""
    result = subprocess.run([sys.executable,ifile,ofile]+[f"{x}={y}" for x,y in options.items()])
    return result.returncode


def convert_pypower(ifile,ofile,options={}):
    """Pypower case converter"""
    autoname = options['autoname'] if 'autoname' in options else True
    modspec = util.spec_from_file_location("glm",ifile)
    modname = os.path.splitext(ifile)[0]
    mod = importlib.import_module(os.path.basename(modname))
    casedef = getattr(mod,os.path.basename(modname))
    data = casedef()

    # check for required data
    for req in ["version","baseMVA","bus","branch","gen"]:
        if req not in data: # fails
            # run as script instead
            return convert_python(ifile,ofile,options)

    NL='\n'
    with open(ofile,"w") as glm:
        glm.write(f"""// generated by {' '.join(sys.argv)}
module pypower
{{
    version {data['version']};
    baseMVA {data['baseMVA']};
}}
""")

        for name,spec in DATASPEC.items():
            glm.write(f"{NL}//{NL}// {name}{NL}//{NL}")
            for n,line in enumerate(data[name]):
                oname = f"""{NL}    name "pp_{name}_{n+1}";""" if autoname else ""
                glm.write(f"""object pypower.{name} 
{{{oname}
""")
                for n,x in enumerate(spec.items()):
                    glm.write(f"    {x[0]} {x[1].format(line[n])};{NL}")
                    if name in MODIFY:
                        for key,value in [(y,z) for y,z in MODIFY[name].items() if x[0] == z[0]]:
                            # print(f"{name=}{NL}{line=}{NL}{n=}{NL}{x=}{NL}{key=}{NL}{value[0]=}{NL}{value[1](line)=}",flush=True,file=sys.stderr)
                            glm.write(f"""    {key} "{value[1](line)}";{NL}""")
                glm.write("}\n")

        if 'gencost' in data:
            glm.write("\n//\n// gencost\n//\n")
            for n,line in enumerate(data['gencost']):
                model = line[0]
                startup = line[1]
                shutdown = line[2]
                count = line[3]
                costs = line[4:]
                assert(len(costs)==count)
                oname = f"{NL}    name pp_gencost_{n+1};" if autoname else ""
                glm.write(f"""object pypower.gencost
{{{oname}
    parent "pp_gen_{n+1}";
    model {int(model)};
    startup {startup};
    shutdown {shutdown};
    costs "{','.join([str(x) for x in costs])}";
}}
""")
    return 0

converters = {
    "python": convert_python,
    "pypower": convert_pypower,
}

if __name__ == '__main__':
    sys.exit(main())

