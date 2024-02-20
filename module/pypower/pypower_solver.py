# module/pypower/pypower_solver.py
# Copyright (C) 2024 Regents of the Leland Stanford Junior University

import os, sys
from pypower.api import case14, ppoption, runpf
from numpy import array

with_opf = False
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

def solver(pf_case):

    try:

        # print(f"solver(pf_case={pf_case})",file=sys.stderr,flush=True)

        casedata = dict(version=str(pf_case['version']),baseMVA=pf_case['baseMVA'])

        # copy from model
        for name in ['bus','gen','branch']:
            casedata[name] = array(pf_case[name])

        if save_case:
            with open("pypower_casedata.py","w") as fh:
                fh.write(str(casedata))

        # TODO: call solver
        # print(f"solver(pf_case={pf_case})",file=sys.stderr,flush=True)
        # stdout = sys.stdout
        # stderr = sys.stderr
        # devnull = open("/dev/null","w")
        # sys.stdout = devnull
        # sys.stderr = devnull
        results,success = runpf(casedata,options)
        # sys.stdout = stdout
        # sys.stderr = stderr
        # devnull.close()

        if save_case:
            with open("pypower_results.py","w") as fh:
                fh.write(str(results))

        # copy back to model
        if success:

            # print("  --> SUCCESS:",results,file=sys.stderr,flush=True)
            for name in ['bus','gen','branch']:
                pf_case[name] = results[name].tolist()
            return True

        else:
            
            # print("  --> FAILED:",results,file=sys.stderr,flush=True)
            return False

    except Exception as err:

        print("  --> EXCEPTION:",err,file=sys.stderr,flush=True)

        return False

