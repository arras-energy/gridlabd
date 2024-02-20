import os, sys
from pypower import runpf
from numpy import array

with_opf = False

def solver(pf_case):

    data = dict(version=pf_case['version'],baseMVA=pf_case['baseMVA'])

    # copy from model
    for name in ['bus','branch','gen']:
        data[name] = array(pf_case[name])

    # TODO: call solver
    runpf(data)

    # copy back to model
    for name in ['bus','branch','gen']:
        pf_case[name] = data[name].tolist()

    print(f"solver(pf_case={pf_case})",file=sys.stderr,flush=True)

    return True

