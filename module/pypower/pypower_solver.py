# module/pypower/pypower_solver.py
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

import os, sys
from pypower.api import case14, ppoption, runpf, runopf
from numpy import array

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

def solver(pf_case):

    try:

        # read options from case
        for key in globals():
            if key in pf_case:
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
            with open("pypower_casedata.py","w") as fh:
                fh.write(str(casedata))

        # run OPF solver if gencost data is found
        if 'gencost' in casedata:
            results = runopf(casedata,options) 
            success = results['success']
        else:
            results,success = runpf(casedata,options) 

        # save results to file
        if save_case:
            with open("pypower_results.py","w") as fh:
                fh.write(str(results))

        # copy back to model
        if success:

            # print("  --> SUCCESS:",results,file=sys.stderr,flush=True)
            for name in ['bus','gen','branch']:
                pf_case[name] = results[name].tolist()
            return pf_case

        else:
            
            # print("  --> FAILED:",results,file=sys.stderr,flush=True)
            return False

    except Exception:

        e_type,e_value,e_trace = sys.exc_info()

        print("EXCEPTION [pypower_solver.py]:",e_type,e_value,file=sys.stderr,flush=True)
        if debug:
            import traceback
            traceback.print_exception(e_type,e_value,e_trace,file=sys.stderr)

        return False

