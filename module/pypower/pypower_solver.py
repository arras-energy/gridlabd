# module/pypower/pypower_solver.py
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

import os, sys
from pypower.api import ppoption, runpf, runopf
from numpy import array, set_printoptions, inf
import json, csv

set_printoptions(threshold=inf,linewidth=inf,formatter={'float':lambda x:f"{x:.6g}"})

# TODO: read these values from the pf_case argument
save_case = False
debug = False
verbose = False
solver_method = 1 # 1=NR, 2=FD-XB, 3=FD-BX, 4=GS
solution_tolerance = 1e-08
maximum_iterations_nr = 10
maximum_iterations_fd = 30
maximum_iterations_gs = 1000
enforce_q_limits = False
use_dc_powerflow = False
save_format = "csv"
modelname = "pypower"

csv_headers = {
    "bus" : "bus_i,type,Pd,Qd,Gs,Bs,area,Vm,Va,baseKV,zone,Vmax,Vmin,lam_P,lam_Q,mu_Vmax,mu_Vmin",
    "branch" : "fbus,tbus,r,x,b,rateA,rateB,rateC,ratio,angle,status,angmin,angmax",
    "gen" : "bus,Pg,Qb,Qmax,Qmin,Vg,mBase,status,Pmax,Pmin,Pc1,Pc2,Qc1min,Qc1max,Qc2min,Qc2max,ramp_agc,ramp_10,ramp_30,ramp_q,apf,mu_Pmax,mu_Pmin,mu_Qmax,mu_Qmin",
    "gencost" : "model,startup,shutdown,parameters",
}

def write_case(data,filename):
    name,ext = os.path.splitext(filename)
    if ext == ".py":
        with open(filename,"w") as fh:
            fh.write(str(data))
    elif ext == ".json":
        def fix(x):
            if hasattr(x,"tolist"):
                return x.tolist()
            if type(x) is list:
                return [fix(y) for y in x]
            if type(x) is dict:
                return dict(zip(list(x.keys()),fix(list(x.values()))))
            if type(x) in [int,str,bool,float,None]:
                return x
            raise Exception(f"cannot fix {type(x)}({x})")
        with open(filename,"w") as fh:
            result = {}            
            for key,value in data.items():
                result[key] = fix(value)
            json.dump(result,fh,indent=2)
    elif ext == ".csv":
        for key,value in data.items():
            if key in ["bus","branch","gen","gencost"]:
                with open(f"{name}_{key}.csv","w") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(csv_headers[key].split(','))
                    for row in value.tolist():
                        writer.writerow(row)


def solver(pf_case):

    try:

        # read options from case
        for key in globals():
            if key in pf_case:
                print("option",key,'=',pf_case[key])
                globals()[key] = pf_case[key]
        options = ppoption(
            PF_ALG = solver_method,
            PF_TOL = solution_tolerance,
            PF_MAX_IT = maximum_iterations_nr,
            PF_MAX_IT_FD = maximum_iterations_fd,
            PF_MAX_IT_GS = maximum_iterations_gs,
            ENFORCE_Q_LIMS = enforce_q_limits,
            PF_DC = use_dc_powerflow,
            OUT_ALL = 1 if debug else 0,
            VERBOSE = 3 if verbose else 0,
            OUT_SYS_SUM = verbose,
            OUT_AREA_SUM = verbose,
            OUT_BUS = verbose,
            OUT_BRTANCH = verbose,
            OUT_GEN = verbose,
            OUT_ALL_LIM = verbose,
            OUT_V_LIM = verbose,
            OUT_LINE_LIM = verbose,
            OUT_PG_LIM = verbose,
            OUT_QG_LIM = verbose,
            )
        for key in options:
            if key in pf_case:
                options[key] = pf_case[key]
        if debug:
            print("ppoptions = {",file=sys.stderr)
            for x,y in options.items():
                print(f"             '{x}' = {repr(y)},")
            print("            }",file=sys.stderr)

        # setup casedata
        casedata = dict(version=str(pf_case['version']),baseMVA=pf_case['baseMVA'])

        # copy from model
        for name in ['bus','gen','branch']:
            if name in pf_case:
                casedata[name] = array(pf_case[name])
        if 'gencost' in pf_case:
            costdata = []
            for cost in pf_case['gencost']:
                costs = [float(x) for x in cost[3].split(',')]
                costdata.append([int(cost[0]),cost[1],cost[2],len(costs)])
                costdata[-1].extend(costs)
            casedata['gencost'] = array(costdata)

        # save casedata to file
        if save_case:
            write_case(casedata,f"{modelname}_casedata.{save_format}")

        # run OPF solver if gencost data is found
        if 'gencost' in casedata:
            results = runopf(casedata,options) 
            success = results['success']
        else:
            results,success = runpf(casedata,options) 

        # save results to file
        if save_case:
            write_case(results,f"{modelname}_results.{save_format}")

        # copy back to model
        if success:

            for name in ['bus','gen','branch']:
                pf_case[name] = results[name].tolist()
            return pf_case

        if not save_case:
            
            write_case(results,f"{modelname}_failed.{save_format}")
        
        return False

    except Exception:

        e_type,e_value,e_trace = sys.exc_info()

        print("EXCEPTION [pypower_solver.py]:",e_type,e_value,file=sys.stderr,flush=True)
        import traceback
        traceback.print_exception(e_type,e_value,e_trace,file=sys.stderr)

        return False

