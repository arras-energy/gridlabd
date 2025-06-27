# module/pypower/pypower_solver.py
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

import os, sys

# fix version issues with numpy and pypower
import numpy
try:
    from numpy import inf
    numpy.Inf = inf 
except:
    from numpy import Inf
    inf = numpy.inf = Inf

from numpy import array, set_printoptions
from pypower.api import ppoption, runpf, runopf
from math import sqrt
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
stop_on_failure = True
maximum_iterations_opf = 20
opf_feasibility_tolerance = 1e-06
opf_gradient_tolerance = 1e-06
opf_condition_tolerance = 1e-06
opf_cost_tolerance = 1e-06

csv_headers = {
    "bus" : "bus_i,type,Pd,Qd,Gs,Bs,area,Vm,Va,baseKV,zone,Vmax,Vmin,lam_P,lam_Q,mu_Vmax,mu_Vmin",
    "branch" : "fbus,tbus,r,x,b,rateA,rateB,rateC,ratio,angle,status,angmin,angmax,Pfrom,Qfrom,Pto,Qto,mu_Sfrom,mu_Sto,mu_angmin,mu_angmax",
    "gen" : "bus,Pg,Qg,Qmax,Qmin,Vg,mBase,status,Pmax,Pmin,Pc1,Pc2,Qc1min,Qc1max,Qc2min,Qc2max,ramp_agc,ramp_10,ramp_30,ramp_q,apf,mu_Pmax,mu_Pmin,mu_Qmax,mu_Qmin",
    "gencost" : "model,startup,shutdown,parameters",
}

class PypowerError(Exception):
    pass

def write_case(data,filename,diagnostics=True):
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

    if diagnostics:
        with open(f"{name}.txt","w") as fh:
            print("*** SOLVER FAILURE DIAGNOSTICS ***\n",file=fh)
            if "gen" in data and len(data["gen"]) > 0 and len(data["gen"][0]) > 9:
                generation_violations = [x for x in sorted(data["gen"],key=lambda x:x[0])
                    if ( x[8] > x[9] and not ( x[9] <= x[1] <= x[8]) ) 
                        or ( x[4] > x[3] and not ( x[4] <= x[2] <= x[3]) )]
                if generation_violations:
                    print("Generation output violations:\n\n",
                        "Bus     Pmin     Pg       Pmax       Qmin     Qg       Qmax\n",
                        "-----   -------- -------- --------   -------- -------- -------- \n",
                        *[f"{int(x[0]):5d}   {x[9]:8.1f} {x[1]:8.1f} {x[8]:8.1f}   {x[4]:8.1f} {x[2]:8.1f} {x[3]:8.1f}\n" 
                            for x in generation_violations],file=fh)
                else:
                    print("- No generation violations detected",file=fh)
            else:
                print("! No generation data returned (enable verbose to see solver output)",file=fh)

            if "branch" in data and len(data["branch"]) > 0 and len(data["branch"][0]) > 13:
                flow_violations = [x for x in sorted(data["branch"],key=lambda x:(x[0],x[1]))
                    if max(x[5:8]) > 0 and max(sqrt(x[13]**2+x[14]**2),sqrt(x[15]**2+x[16]**2)) > max(x[5:8])]
                if flow_violations:
                    print("Branch flow violations:\n\n",
                        "From  To      Pin      Qin        Pout     Qout       Smax\n",
                        "----- -----   -------- --------   -------- --------   --------\n",
                        *[f"{int(x[0]):5d} {int(x[1]):5d}   {x[13]:8.1f} {x[14]:8.1f}   {x[15]:8.1f} {x[16]:8.1f}   {max(x[5:8])}\n" 
                            for x in flow_violations],file=fh)
                else:
                    print("- No flow violations detected",file=fh)
            else:
                print("! No branch data returned (enable verbose to see solver output)",file=fh)

            if "bus" in data and len(data["bus"]) > 0 and len(data["bus"][0]) > 12:
                voltage_violations = [x for x in sorted(data["bus"],key=lambda x:x[0])
                    if x[11] > x[12] and not (x[12] <= x[7] <= x[11])]
                if voltage_violations:
                    print("Bus voltage violations:\n\n",
                        "Bus   Vmin  Vmag  Vmax\n",
                        "----- ----- ----- -----\n",
                        *[f"{int(x[0]):5d} {x[12]:5.3f} {x[7]:5.3f} {x[11]:5.3f}\n" 
                            for x in voltage_violations],file=fh)
                else:
                    print("- No voltage violations detected",file=fh)
            else:
                print("! No bus data returned (enable verbose to see solver output)",file=fh)


def jsonify(data):
    if type(data) is dict:
        result = {}
        for x,y in data.items():
            if type(y) in [int,str,float,bool]:
                result[x] = y
            elif hasattr(y,"tolist"):
                if x in ["bus","branch","gen"]:
                    result[x] = f"{modelname.replace(os.getcwd(),'.')}_results_{x}.csv"
                else:
                    result[x] = y.tolist()
            elif type(y) in [list,dict]:
                result[x] = jsonify(x)
    elif type(data) is list:
        result = []
        for x in data:
            if type(y) in [int,str,float,bool]:
                result.append(y)
            elif hasattr(y,"tolist"):
                result.append(y.tolist())
            elif type(y) in [list,dict]:
                result.append(jsonify(x))
    # print(result,file=sys.stderr,flush=True)
    else:
        result = data
    return result

def solver(pf_case):

    try:

        # read options from case
        for key in globals():
            if key in pf_case:
                globals()[key] = pf_case[key]
                if debug:
                    print("option",key,'=',pf_case[key],file=sys.stderr)
        options = ppoption(
            PF_ALG = solver_method,
            PF_TOL = solution_tolerance,
            PF_MAX_IT = maximum_iterations_nr,
            PF_MAX_IT_FD = maximum_iterations_fd,
            PF_MAX_IT_GS = maximum_iterations_gs,
            ENFORCE_Q_LIMS = enforce_q_limits,
            PF_DC = use_dc_powerflow,
            OUT_ALL = 1 if verbose else 0,
            VERBOSE = 3 if debug else 0,
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
            PDIPM_MAX_IT = maximum_iterations_opf,
            PDIPM_FEASTOL = opf_feasibility_tolerance,
            PDIPM_GRADTOL = opf_gradient_tolerance,
            PDIPM_COMPTOL = opf_condition_tolerance,
            PDIPM_COSTTOL = opf_cost_tolerance,
            )
        for key in options:
            if key in pf_case:
                options[key] = pf_case[key]
        if debug:
            print("ppoptions = {",file=sys.stderr)
            for x,y in options.items():
                print(f"             '{x}' = {repr(y)},",file=sys.stderr)
            print("            }",file=sys.stderr)

        # setup casedata
        casedata = dict(version=str(pf_case['version']),baseMVA=pf_case['baseMVA'])

        # copy from model
        for name in ['bus','branch']:
            if name in pf_case:
                casedata[name] = array(pf_case[name])

        # output detailed solver debugging information 
        if debug and verbose:

            print(f"\n*** BUS DATA ***\n",file=sys.stderr)
            print("BUS_I BUS_TYPE   PD      PQ      GS      BS    BUS_AREA  VM    VA   BASE_KV ZONE VMAX  VMIN",file=sys.stderr)
            print("----- -------- ------- ------- ------- ------- -------- ----- ----- ------- ---- ----- -----",file=sys.stderr)
            for row in sorted(casedata["bus"],key=lambda x:x[0]):
                print(f"{row[0]:5.0f} {['?','PQ','PV','REF','ISOLATED'][int(row[1])]:8.8s}"
                    + f" {row[2]:7.1f} {row[3]:7.1f} {row[4]:7.1f} {row[5]:7.1f}"
                    + f" {row[6]:8.0f} {row[7]:5.3f} {row[8]:5.1f} {row[9]:7.1f}"
                    + f" {row[10]:4.0f} {row[11]:5.1f} {row[12]:5.1f}"
                    ,file=sys.stderr)

            print(f"\n*** BRANCH DATA ***\n",file=sys.stderr)
            print("F_BUS T_BUS   BR_R     BR_X     BR_B   RATE_A RATE_B RATE_C  TAP  SHIFT BR_STATUS ANGMIN ANGMAX",file=sys.stderr)
            print("----- ----- -------- -------- -------- ------ ------ ------ ----- ----- --------- ------ ------",file=sys.stderr)
            for row in sorted(casedata["branch"],key=lambda x:(x[0],x[1])):
                print(f"{row[0]:5.0f} {row[1]:5.0f} {row[2]:8.5f} {row[3]:8.5f} {row[4]:8.5f}"
                    + f" {row[5]:6.0f} {row[6]:6.0f} {row[7]:6.0f} {row[8]:5.2f} {row[9]:5.1f}"
                    + f" {['OUT','IN'][int(row[10])]:9.9s} {row[11]:6.1f} {row[12]:6.1f}"
                    ,file=sys.stderr)

        if 'gen' in pf_case:
            genmap = [n for n,x in enumerate(pf_case['gen']) if x[7] == 1]
            casedata['gen'] = array([pf_case['gen'][n] for n in genmap])

        # output detailed solver debugging information 
        if debug and verbose:

            print(f"\n*** GEN DATA ***\n",file=sys.stderr)
            print("GEN   GEN_BUS    PG       QG      QMAX     QMIN   VG    MBASE GEN_STATUS PMAX  PMIN   PC1   PC2  QC1MIN QC1MAX QC2MIN QC2MAX RAMP_AGC RAMP_10 RAMP_30 RAMP_Q  APF ",file=sys.stderr)
            print("----- ------- -------- -------- -------- -------- ----- ----- ---------- ----- ----- ----- ----- ------ ------ ------ ------ -------- ------- ------- ------ -----",file=sys.stderr)
            for n,row in enumerate(casedata["gen"]):
                print(f"{float(genmap[n]):5.0f} {row[0]:7.0f} {row[1]:8.1f} {row[2]:8.1f} {row[3]:8.0f} {row[4]:8.0f}"
                    + f" {row[5]:5.3f} {row[6]:5.0f} {['OUT','IN'][int(row[7])]:10.10s} {row[8]:5.0f} {row[9]:5.0f}"
                    + f" {row[10]:5.0f} {row[11]:5.0f} {row[12]:6.1f} {row[13]:6.1f} {row[14]:6.1f} {row[15]:6.1f}"
                    + f" {row[16]:8.1f} {row[17]:7.1f} {row[18]:7.1f} {row[19]:6.1f} {row[20]:5.2f}"
                    ,file=sys.stderr)

        # copy gencosts only for OPF problems
        if 'gencost' in pf_case and 'gen' in pf_case:
            costdata = []
            for cost in [x for n,x in enumerate(pf_case['gencost']) if pf_case['gen'][n][7] == 1]:
                costs = [float(x) for x in cost[3].split(',')]
                costdata.append([int(cost[0]),cost[1],cost[2],len(costs)])
                costdata[-1].extend(costs)
            casedata['gencost'] = array(costdata)
            
            # output detailed solver debugging information 
            if debug and verbose:
                print("")
                # print(f"\n*** GENCOST DATA ***\n\n{casedata['gencost']}",file=sys.stderr)
                # for row in sorted(casedata['gencost'],key=lambda x:x[0])
                print("\n*** GENCOST DATA ***\n",file=sys.stderr)
                print("GEN   MODEL STARTUP SHUTDOWN NCOST COST",file=sys.stderr)
                print("----- ----- ------- -------- ----- -----------------------",file=sys.stderr)
                for n,row in enumerate(casedata["gencost"]):
                    print(f"{float(genmap[n]):5.0f} {['-','PWLF','POLY'][int(row[0])]:5.5s} {row[1]:7.2f} {row[2]:8.2f} {row[3]:5.0f} {','.join([str(x) for x in row[4:]])}",file=sys.stderr)

        # save casedata to file
        if save_case:
            write_case(casedata,f"{modelname}_casedata.{save_format}",False)

        # check for at least one REF or PV bus
        if len([x[0] for x in casedata['bus'] if x[1] in [2,3]]) == 0:
            raise PypowerError("no REF or PV bus found")

        # run OPF solver if gencost data is found
        if 'gencost' in casedata:
            if len(casedata['gencost']) > 0:
                results = runopf(casedata,options) 
                success = results['success']
            else:
                raise PypowerError("cannot solve OPF without gencost data")
        else:
            results,success = runpf(casedata,options) 

        # save results to file
        if save_case:
            write_case(results,f"{modelname}_results.{save_format}",False)
            with open(f"{modelname}_results_solver.json","w") as fh:
                
                json.dump(jsonify(results),fh,indent=2) 

        sys.stdout.flush()
        sys.stderr.flush()

        # copy back to model
        if not success:

            write_case(results,f"{modelname}_failed.{save_format}")

            if stop_on_failure:
                return False
            
        for name in ['bus','branch']:
            pf_case[name] = results[name].tolist()
        for n,m in enumerate(genmap):
            pf_case['gen'][m] = results['gen'][n].tolist()

        return pf_case
        

    except Exception:

        write_case(casedata,f"{modelname}_exception.{save_format}",False)

        e_type,e_value,e_trace = sys.exc_info()
        print(f"EXCEPTION [{os.path.basename(e_trace.tb_frame.f_code.co_filename)}@{e_trace.tb_lineno}]: {e_type.__name__} - {e_value}",file=sys.stderr,flush=True)
        if debug:
            import traceback
            traceback.print_exception(e_type,e_value,e_trace,file=sys.stderr)

        return False

